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

cfg=None

class UpdateNotNeeded(Exception):
  '''
  Custom exception
  '''
  def __init__(self,*args,**kwargs):
    Exception.__init__(self,*args,**kwargs)

class RecordUpdated(Exception):
  '''
  Custom exception
  '''
  def __init__(self,*args,**kwargs):
    Exception.__init__(self,*args,**kwargs)


class Db:
  '''
  This class is responsible for handling sql operations
  '''
  def __init__(self,cfg):
    self.conn=None
    self.cur=None

    dbconf = cfg.get('mariadb',None)
    if dbconf != None:
      try:
        dbconf['connection_timeout'] = int(dbconf['connection_timeout'])
        self.conn = mariadb.connect(**dbconf)
        self.cur = self.conn.cursor()
      except Exception as e:
        raise e

    dbconf = cfg.get('postgres',None)
    if dbconf != None:
      raise NotImplementedError("Postgresql is not supported yet !")

  def __del__(self):
    self.conn.close()

  def soa_bumpup(self,name):
    '''
    This method bumps up SOA serial every time we change record
    It also preserves SN format avoidint overlaps
    '''
    domain='.'.join(name.strip().split('.')[1:])

    try:
      self.cur.execute( "SELECT id,content FROM records WHERE type='SOA' AND name='%s'" % (domain), )
    except Exception as e:
      self.__del__()
      raise e

    out = self.cur.fetchall()
    if len(out) != 1:
      self.__del__()
      raise ValueError("More than one or zero 'SOA' records matched")

    id=out[0][0]
    soa=out[0][1].strip()
    soa_array=soa.split()

    #soa woodoo begins here
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
      self.cur.execute( "UPDATE records SET content = '%s' WHERE type='SOA' and id=%d" % (str(soa),id) ,  )
    except Exception as e:
      self.__del__()
      raise e

    raise RecordUpdated("")

  def update_A(self,name,value):
    '''
    This one updates 'A' records and also triggers soa_bumpup. First step is IP addr validation
    '''

    try:
      socket.inet_aton(value)
    except socket.error:
      raise Exception("This is not an ip address !")

    try:
      self.cur.execute("SELECT content FROM records where type='A' and name='%s'" % (str(name)),)
    except Exception as e:
      self.__del__()
      raise e

    out = self.cur.fetchall()
    if len(out) != 1:
      self.__del__()
      raise ValueError("More than one or zero 'A' records matched")

    current_value = str(out[0][0]).strip()

    if current_value != value:
      try:
        self.cur.execute( "UPDATE records SET content = '%s' WHERE type='A' AND name='%s'" % (str(value),str(name)) ,  )
      except Exception as e:
        self.__del__()
        raise e
      try:
        self.soa_bumpup(name)
      except RecordUpdated as e:
        pass
      except Exception as e:
        self.__del__()
        raise e
      self.conn.commit()
      raise RecordUpdated("Record updated")
    else:
      raise UpdateNotNeeded("No update needed")




@app.route('/update', methods=['POST'])
def update():
  global cfg

  req = request.get_json()
  user = req.get('user', None)
  pswd = req.get('pswd', None)
  fqdn = req.get('fqdn', None)
  value = req.get('value', None)

  if user == None or pswd == None:
    #please provide this two variables via post
    return "Invalid creds", 403

  userdef = cfg['creds'].get(user, None)
  pswd = hashlib.sha512(pswd.encode('utf-8')).hexdigest()
  if userdef == None:
    #nonexistient user
    return "Invalid creds", 403

  if userdef['pass'] != pswd:
    #incorrect password
    return "Invalid creds", 403

  #request lacking a parameter fqdn will alter first record on a list
  if fqdn != None:
    if fqdn not in userdef['records']:
  	   return "You are not allowed to tackle with this record", 400
  else:
    fqdn = cfg['creds'][user]['records'][0]

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

  d=Db(cfg)
  try:
    d.update_A(fqdn,value)
  except RecordUpdated as e:
    del d
    return "Updated", 200
  except UpdateNotNeeded as e:
    del d
    return "Update not needed", 201
  except Exception as e:
    return str(e), 500





def init():
  global cfg

  if cfg == None:
    try:
      f=open("/etc/pdnsupdater/config.json")
      cfg=json.load(f)
    except Exception as e:
      print("Unable to load configuration file ... %s" % (str(e)))
      sys.exit(-1)

    f.close()

init()

if __name__ == "__main__":
  init()
  app.run(host=cfg['listen']['host'],port=int(cfg['listen']['port']))
