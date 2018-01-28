# pdnsupdater
Simple Flask API Gateway for updating pDNS database records


This app can be used for updating existing A records like that:

curl -k -v -H "Content-Type: application/json" -X POST -d '{"user":"username", "pswd":"yourpass", "value":"1.1.1.1"}'  https://localhost:8888/update

Parameters like value and fqdn are optional. If ommited app will default to request source address and to the first entitled fqdn.


Dependencies:
flask
mysql-connector-python


Starting application:

!! First prepare configuration /etc/pdnsupdater/config.json

Starting for development:
python pdnsupdater

!! Note this starts builtin wsgi server without SSL. Anyone can intercept your password ...


More reasonable way of starting:
-use gunicorn with built-in ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $(hostname -s).key -out $(hostname -s).crt
gunicorn -b 0.0.0.0:8443 -w 2 --keyfile $(hostname -s).key --certfile $(hostname -s).crt pdnsupdater:app


-use nginx+gunicorn
-use apache+wsgi+gunicorn



Todos:

Refactor/Cleanup
Modular construction that allows different db's (at least Postgresql)
More reasonable input validation ;)
