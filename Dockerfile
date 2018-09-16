FROM alpine:3.8
RUN apk add --no-cache py3-flask py3-pip py3-gunicorn

RUN pip3 install mysql-connector-python && \
  mkdir -p /opt/app /etc/pdnsupdater

ADD pdnsupdater.py /opt/app/pdnsupdater.py
RUN chmod 755 /opt/app/pdnsupdater.py

WORKDIR /opt/app

ENTRYPOINT ["/usr/bin/gunicorn"]
CMD ["-b", ":8888", "--workers=2", "--access-logfile=-", "--error-log=-", "--keyfile=/etc/pdnsupdater/server.key", "--certfile=/etc/pdnsupdater/server.crt", "pdnsupdater:app"]
