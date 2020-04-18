# Installing Postgres and configuring it for Django

To install postgres just run: 

```shell script
brew install postgresql
```

start a Postgresql server:

```shell script
brew services start postgresq
```

try logging in:

```shell script
psql
```

If login fails with "Database <user> does not exist", create your <user> db:

```shell script
createdb
```

and try logging in again. When login successful, create database for your project:

```postgresql
CREATE DATABASE myproject;
```

create role, which your server will use to access this database:

```postgresql
CREATE USER myprojectuser WITH PASSWORD 'password';
```

set encodings, expected by Django:

```postgresql
ALTER ROLE myprojectuser SET client_encoding TO 'utf8';
ALTER ROLE myprojectuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE myprojectuser SET timezone TO 'UTC';
```

and exit SQL prompt with `\q`
