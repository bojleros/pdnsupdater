# pdnsupdater
Simple Flask API Gateway for updating pDNS database records

### Description
This app can be used for updating existing A records in a quite simple way:

```
curl -k -v -H "Content-Type: application/json" -X POST -d '{"user":"username", "pswd":"yourpass", "fqdn" : "mail.example.net", "value":"1.1.1.1"}'  https://localhost:8888/update
```

Pdnsupdater connects DB backend and directly alters records. You can even ommit some parameters so client ip address will be used for updating user's first record:

```
curl -k -v -H "Content-Type: application/json" -X POST -d '{"user":"username", "pswd":"yourpass"}'  https://localhost:8888/update
```


### Dependencies

```
flask
mysql-connector-python
```


### Starting application

1. Generate password hashes for your users. You can use interactive python shell but don't forget to import hashlib !
2. Prepare configuration /etc/pdnsupdater/config.json or ~/config.json
3. Generate password

```
$ python
Python 2.7.15 (default, May 16 2018, 17:50:09)
[GCC 8.1.1 20180502 (Red Hat 8.1.1-1)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import hashlib
>>> hashlib.sha512('yourpass').hexdigest()
'26de4aa397ef5562ca16ce2c9b9c335ca468f700fedc5a052ac66b98b3f817b81ff3c6449820f548cd279965e3f9353025709ecf1d6126ee37d354d16bacd57f'
>>>
```

4. Decide if you want to put your credentials into config.json or into database itself.

- config.json - look for examples directory
- databse - you need to create following tables and records and include "creds_from" : "db" into the config.json

```
use your_pdns_database;
CREATE TABLE pdnsu_users
(
  uid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user varchar(32) NOT NULL,
  pass varchar(512) NOT NULL
);

CREATE TABLE pdnsu_domains
(
  did INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  uid INT NOT NULL,
  domain varchar(128) NOT NULL
);

insert into pdnsu_users (user,pass) values('test','26de4aa397ef5562ca16ce2c9b9c335ca468f700fedc5a052ac66b98b3f817b81ff3c6449820f548cd279965e3f9353025709ecf1d6126ee37d354d16bacd57f');


select uid from pdnsu_users where user='test';
#now use this uid for inserting dns records for your users

insert into pdnsu_domains (uid,domain) values(1,'vader.example.com');
insert into pdnsu_domains (uid,domain) values(1,'yoda.example.com');

#test user is now entitled to update this two domains and api will fall back to the first one if you specify none in api call
```

### Starting for development
python pdnsupdater

!! Note this starts builtin wsgi server without SSL. Anyone can intercept your password ...


### More reasonable way of starting

#### Use container (with ssl)

```
# ls /pdnsu/
config.json  server.crt  server.key
# docker run --rm --name pdnsu -v /pdnsu:/etc/pdnsupdater -p 8888:8888 bojleros/pdnsupdater
```

#### Use standalone gunicorn with built-in ssl

```
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt
gunicorn -b 0.0.0.0:8443 -w 2 --keyfile server.key --certfile server.crt pdnsupdater:app
```

#### Use nginx+gunicorn

TBD.

#### Use apache+wsgi+gunicorn

TBD.

###Todos

Modular or semi-modular construction that allows different db's (at least Postgresql)
More reasonable input validation ;)
