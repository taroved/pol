#!/bin/bash

sed -i -E -e "s/(DEBUG = ).*/\1True/" \
    -e "s/('NAME': ')pol(',)/\1${DB_NAME}\2/" \
    -e "s/('USER': ')root(',)/\1${DB_USER}\2/" \
    -e "s/('PASSWORD': ')toor(',)/\1${DB_PASSWORD}\2/" \
    -e "s/('HOST': ')127\.0\.0\.1(',)/\1${DB_HOST}\2/" \
    -e "s/('PORT': ')3306(',)/\1${DB_PORT}\2/" \
    -e "s/(TIME_ZONE = ').*/\1${TIME_ZONE}'/" \
    ./frontend/frontend/settings.py

sed -i -e 's/listen\ 80/listen\ '${WEB_PORT}'/g' \
    -e 's/\[::\]:80/\[::\]:'${WEB_PORT}'/g' /etc/nginx/sites-available/default \
    && service nginx reload

service nginx start > /dev/null

/usr/bin/python ./frontend/manage.py migrate 
/usr/bin/python ./frontend/manage.py loaddata fields.json 

/usr/bin/python ./downloader.py &
/usr/bin/python ./frontend/manage.py runserver
