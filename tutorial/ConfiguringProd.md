#Configuring for Production

Under construction - sorry for that. Here I'll share my configuration.

##1. VPS

I have rented a 1 CPU 1GB RAM "Debian 10" machine for 1.5 eur/month. 
It is not much but is enough to play with my friends.
My hosting had Nginx, Postgres and Redis available out-of-the-box.

##2. Project setup

Next step was to git clone this repo and go once again through chapters 
InstallPostgres.md, ProjectSetup.md, InstallDjango.md .

Important part here not to store DB user password in Django's settings.py .
TODO for myself: cover this part

##3. Serving Gunicorn

Gunicorn is an app that helps you utilize your machine resources efficiently.
It will create multiple proccesses to help you deal with high loads of traffic.
Gunicorn will serve wsgi part of Django for you.

TODO: add commands to install gunicorn3 and add it to systemctl, add required configs in nginx

##4. Serving Daphne
The other part of our project is asgi. This one is served with daphne.

TODO: add commands to install daphne and add it to systemctl, add required configs in nginx

##5. HTTPS support: Adding SSL Certificate 

