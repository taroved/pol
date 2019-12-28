#!/bin/sh
# wait until MySQL is really available
maxcounter=100

host="$1"

counter=1
while ! mysql --protocol TCP -h "$host" -u"$DB_USER" -p"$DB_PASSWORD" -e "show databases;" > /dev/null 2>&1; do
    sleep 1
    counter=`expr $counter + 1`
    if [ $counter -gt $maxcounter ]; then
        >&2 echo "We have been waiting for MySQL too long already; failing."
        exit 1
    fi;
done

/bin/bash ./frontend/start.sh
