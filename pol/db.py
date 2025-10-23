import psycopg2
import psycopg2.extras


def get_conn(creds, dict_result=False):
    cursor_factory = psycopg2.extras.RealDictCursor if dict_result else None
    db = psycopg2.connect(
        host=creds['HOST'],
        port=int(creds['PORT']),
        user=creds['USER'],
        password=creds['PASSWORD'],
        dbname=creds['NAME'],
        cursor_factory=cursor_factory
    )
    db.autocommit = True
    return db
