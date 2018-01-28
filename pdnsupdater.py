#!/usr/bin/python

import time
import sys
import os
import json
import socket
import time
import hashlib

from flask import Flask
from flask import request
import logging
import logging.handlers
import mysql.connector as mariadb
from mysql.connector import errorcode

app = Flask(__name__)
app.debug = True

opts=list()

@app.route('/update', methods=['POST'])
def update():
	global opts
	conf, lh = opts

	req = request.get_json()
	user = req.get('user', None)
	pswd = req.get('pswd', None)
	fqdn = req.get('fqdn', None)
	value = req.get('value', None)

	#we need input validation here and now

	if user == None or pswd == None:
		#please provide this two variables via post
		lh.warning("%s@%s Invalid creds" % ("unknown",str(request.remote_addr)) )
		return "Invalid creds", 403
	
	userdef = conf['creds'].get(user, None)
	pswd = hashlib.sha512(pswd).hexdigest()
	if userdef == None:
		#nonexistient user
		lh.warning("%s@%s No such user" % ("unknown",str(request.remote_addr)) )
		return "Invalid creds", 403
	
	if userdef['pass'] != pswd:
		#incorrect password
		lh.warning("%s@%s Incorrect password" % (str(user),str(request.remote_addr)) )
		return "Invalid creds", 403
	
	lh.warning("%s@%s Correct credentials" % (str(user),str(request.remote_addr)) )
		
	#request lacking a parameter fqdn will alter first record on a list
	if fqdn != None:
		if fqdn not in userdef['records']:
			return "You are not allowed to tackle with this record", 400
	else:
		fqdn = conf['creds'][user]['records'][0]

	domain = '.'.join(fqdn.split('.')[1:])
	hostn = fqdn[0]

	#request with no value field will update record with a peer address
	if value != None:	
		try:
			socket.inet_aton(value)
		except:
			return "Invalid IP address", 400
	else:
		value = request.remote_addr
	
	value=str(value)


	#mariadb.connect() accepts dictionary of parameters :)
	dbconf=conf.get('mariadb',None)
	if dbconf==None:
		lh.error("No database config under mariadb key")
        	return "Database connection error", 500
	dbconf['connection_timeout'] = float(dbconf['connection_timeout'])
	
	try:
		conn = mariadb.connect(**dbconf)
	except Exception as e:
		lh.error("Unable to connect database : {}".format(str(e)))
		return "Database connection error", 500

	try:
		cur = conn.cursor()
	except Exception as e:
		conn.close()
        	lh.error("Unable to open cursor : {}".format(str(e)))
                return "Database cursor opening error", 500


	#get domainid
	try:
		cur.execute( "SELECT id FROM domains WHERE name = '%s'" % (str(domain)) ,)
	except Exception as e:
		conn.close()
                lh.error("SQL Error : {}".format(str(e)))
                return "SQL Error", 500
		
	out = cur.fetchall()
	if len(out) != 1:
		conn.close()
                lh.error("Domain matching error : {}".format(str(e)))
                return "Data error", 500
	
	domain_id = out[0][0]
	
	#get current ip for this record
	try:
                cur.execute( "SELECT content FROM records WHERE type='A' AND name='%s' and domain_id=%d" % (str(fqdn),domain_id) , )
        except Exception as e:
                conn.close()
                lh.error("SQL Error : {}".format(str(e)))
                return "SQL Error", 500

	out = cur.fetchall()
	if len(out) != 1:
		conn.close()
                lh.error("Record A matching error : {}".format(str(e)))
                return "Data error", 500

	cur_ip_a = str(out[0][0])

	if cur_ip_a != value:
		#Ip is different , we must update
		try:
			cur.execute( "UPDATE records SET content = '%s' WHERE type='A' AND name='%s' and domain_id=%d" % (str(value),str(fqdn),domain_id) ,  )
		except Exception as e:
			conn.close()
	                lh.error("Record A update error : {}".format(str(e)))
        	        return "Update error", 500
		try:
			cur.execute( "SELECT content FROM records WHERE type='SOA' AND domain_id=%d" % (domain_id), )
		except Exception as e:
                        conn.close()
                        lh.error("Get SOA content error : {}".format(str(e)))
                        return "Update error", 500
		
		out = cur.fetchall()
		if len(out) != 1:
                        conn.close()
                        lh.error("More than one SOA !?!?! : {}".format(str(e)))
                        return "Update error", 500
		
		#it's time for SOA arithmetics adventure
		soa = str(out[0][0]).strip()
		soa_array = soa.split()

		domainsn=int(soa_array[2])
	        sn = domainsn % 100
        	dat = str(domainsn / 100)
	        now = time.strftime("%Y%m%d")

        	if dat == now:
                	sn +=1
                	if sn >99:
                        	sn=0
                	newsn = "%s%02d" % (dat,sn)
	        else:
        	        newsn = now + "00"
		
		soa_array[2] = str(newsn)
		soa = ' '.join(soa_array)
		
		try:
			cur.execute( "UPDATE records SET content = '%s' WHERE type='SOA' and domain_id=%d" % (str(soa),domain_id) ,  )
		except Exception as e:
			conn.close()
                        lh.error("SOA update error : {}".format(str(e)))
                        return "Update error", 500

		lh.warning("%s@%s Updated %s => %s" % (str(user),str(request.remote_addr),fqdn,str(value),) )
		conn.commit()
	        cur.close()
        	conn.close()


	        return "Updated",200


	lh.warning("%s@%s Record %s is up to date" % (str(user),str(request.remote_addr),fqdn) )
	cur.close()
	conn.close()
		

	return "Up to date",200


def init():
	global opts
	
	with open("/etc/pdnsupdater/config.json") as cf:
		cfg=json.load(cf)
	
	lh = logging.getLogger('pdnsupdater')
	lh.setLevel(logging.WARNING)

	h = logging.handlers.SysLogHandler(address = '/dev/log')

	lh.addHandler(h)

	opts= cfg, lh

	lh.info("pdnsupdater started")

init()

if __name__ == "__main__":
	global opts
        conf, lh = opts
	app.run(host=conf['listen']['host'],port=int(conf['listen']['port']))


