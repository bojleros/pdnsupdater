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

First generate password hashes for your users. You can use interactive python shell but don't forget to import hashlib !
Second prepare configuration /etc/pdnsupdater/config.json or ~/config.json

### Starting for development
python pdnsupdater

!! Note this starts builtin wsgi server without SSL. Anyone can intercept your password ...


### More reasonable way of starting

#### Use gunicorn with built-in ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $(hostname -s).key -out $(hostname -s).crt
gunicorn -b 0.0.0.0:8443 -w 2 --keyfile $(hostname -s).key --certfile $(hostname -s).crt pdnsupdater:app


#### Use nginx+gunicorn

TBD.

#### Use apache+wsgi+gunicorn

TBD.

###Todos

Modular or semi-modular construction that allows different db's (at least Postgresql)
More reasonable input validation ;)
