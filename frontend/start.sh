#!/bin/bash


service nginx start > /dev/null

/usr/bin/python manage.py migrate 
/usr/bin/python manage.py loaddata fields.json 

/usr/bin/python ../downloader.py &
/usr/bin/python manage.py runserver 
