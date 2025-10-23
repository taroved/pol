#!/bin/bash

sed -i -E -e "s/(DEBUG = ).*/\1True/" \
    -e "s/('NAME': ')politepol(')/\1${DB_NAME}\2/" \
    -e "s/('USER': ')poluser(')/\1${DB_USER}\2/" \
    -e "s/('PASSWORD': ')polpassword(')/\1${DB_PASSWORD}\2/" \
    -e "s/('HOST': ')127\.0\.0\.1(')/\1${DB_HOST}\2/" \
    -e "s/('PORT': ')5432(')/\1${DB_PORT}\2/" \
    -e "s/(TIME_ZONE = ').*/\1${TIME_ZONE}'/" \
    -e "s/'ENGINE': 'django.db.backends.mysql'/'ENGINE': 'django.db.backends.postgresql'/" \
    ./frontend/frontend/settings.py

sed -i -e 's/listen\ 80/listen\ '${WEB_PORT}'/g' \
    -e 's/\[::\]:80/\[::\]:'${WEB_PORT}'/g' /etc/nginx/sites-available/default \
    && service nginx reload

service nginx start > /dev/null

python3 ./frontend/manage.py migrate 
python3 ./frontend/manage.py loaddata fields.json 
python3 ./frontend/manage.py collectstatic --noinput

python3 ./downloader.py &
python3 ./frontend/manage.py runserver 0.0.0.0:${WEB_PORT}
