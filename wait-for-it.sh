#!/bin/sh
# wait until PostgreSQL is really available
maxcounter=100

host="$1"
shift
port="${DB_PORT:-5432}"

counter=1
echo "Waiting for PostgreSQL at $host:$port..."
while ! pg_isready -h "$host" -p "$port" -U "$DB_USER" > /dev/null 2>&1; do
    sleep 1
    counter=`expr $counter + 1`
    if [ $counter -gt $maxcounter ]; then
        >&2 echo "We have been waiting for PostgreSQL too long already; failing."
        exit 1
    fi;
done

echo "PostgreSQL is ready!"
exec "$@"
