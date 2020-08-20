# Configuring for Production

Under construction - sorry for that. Here I'll share my configuration.

## 1. VPS

I have rented a 1 CPU 1GB RAM "Debian 10" machine for 1.5 eur/month. 
It is not much but is enough to play with my friends.
My hosting had Nginx, Postgres and Redis available out-of-the-box.

## 2. Project setup

Next step was to git clone this repo and go once again through chapters `InstallPostgres.md`, `ProjectSetup.md`, `InstallDjango.md`.

Important part here not to store DB user password in Django's `settings.py`.
(TODO: cover this part)

After installations you need to edit `djixit/settings.py`. Make sure `PRODUCTION` variable is set to `True` 
and change static path to `STATIC_ROOT`. To do so uncomment `STATIC_ROOT` line and comment `STATIC_DIRS`. Result should look this way:

```python
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
#STATICFILES_DIRS = [
#    os.path.join(BASE_DIR, "static"),
#]
```

From project root directory run the script to bring static Django admin files:

```shell script
python manage.py collectstatic 
```

To create database tables run:

```shell script
python manage.py makemigrations dixit  #do so for each game
python manage.py migrate
```

## 3. Serving Gunicorn

Gunicorn is an app that helps you utilize your machine resources efficiently.
It will create multiple proccesses to help you deal with high loads of traffic.
Gunicorn will serve wsgi part of Django for you.

TODO: add commands to install gunicorn3 and add it to systemctl, add required configs in nginx

## 4. Serving Daphne
The other part of our project is asgi. This one is served with daphne.

TODO: add commands to install daphne and add it to systemctl, add required configs in nginx

## 5. HTTPS support: Adding SSL Certificate 


## 6. Finalizing

When you have tested everything and ensured no errors occur, it's time to go to `djixit/settings.py` and set `DEBUG` to `False`

useful commands:

```shell script
systemctl restart gunicorn
systemctl restart daphne
systemctl restart nginx
systemctl daemon-reload
systemctl restart daphne
systemctl stop daphne
systemctl start daphne
systemctl status gunicorn
journalctl -u gunicorn
journalctl -u daphne
```

`nano /etc/systemd/system/daphne.service` output:

```shell script
[Unit]
Description=daphne daemon
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/root/Djixit
ExecStart=/usr/local/bin/daphne \
          -u /run/daphne.sock \
          djixit.asgi:application

[Install]
WantedBy=multi-user.target
```

`nano /etc/systemd/system/gunicorn.service` output:

```shell script
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/root/Djixit
ExecStart=/usr/bin/gunicorn3 \
          --access-logfile - \
          --workers 2 \
          --bind unix:/run/gunicorn.sock \
          djixit.wsgi:application

[Install]
WantedBy=multi-user.target
```

`nano /etc/nginx/sites-enabled/Djixit` output:

```shell script
server {
    listen 80;
    server_name <your_domain_here>;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /ws/ {
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";

        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_pass http://unix:/run/daphne.sock;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}

```

`nano /etc/nginx/nginx.conf` http part:

```shell script
http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;

    keepalive_timeout  65;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```