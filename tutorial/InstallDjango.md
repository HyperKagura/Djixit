# Installing Django

Installation itself is pretty simple. Run:

```shell script
pip install django
```

NB! Before you continue make sure to Install Postgres! check out InstallPostgres.md tutorial.

To use Postgres from Django you will need to install popular python postgres package psycopg2:

```shell script
pip install psycopg2
```

If you have issues with installing it, this [stackowerflow post](https://stackoverflow.com/questions/26288042/error-installing-psycopg2-library-not-found-for-lssl/56146592#56146592?newreg=235aab2189fc4cf8b92ef1f26a662f68) was useful for me. I ran
```shell script
brew link openssl
```
and run suggested export LDFLAGS and CPPFLAGS commands, that look like this:
```shell script
export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"
```

and re-tried installing psycopg. Not sure if you should add those exports to zsh profile. (No kidding with openssl - this is a package for your security!)

This repo already has base structure that was created with the following command. You *don't* need to run it.

```shell script
django-admin.py startproject myproject .
```

This command creates a "startproject" with all the files you need.

At this point you might also want to add git tracking to your project. Do it via console or your favorite IDE.

Navigate to `startproject/startproject/settings.py`, find `DATABASES` block and set variables to use your postgres table:

```shell script
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'myproject',
        'USER': 'myprojectuser',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

Now we need to apply changes to the project. run the following from project root dir:

```shell script
python manage.py makemigrations
python manage.py migrate
```

Let's create admin user for our site

```shell script
python manage.py createsuperuser
```

Now let's run our Django site. Do:

```shell script
python manage.py runserver
```

and open your Browser at http://127.0.0.1:8000/ . Hope it worked for you. Now, let's try to log-in as admin. Visit http://127.0.0.1:8000/admin/ and enter your credentials.
