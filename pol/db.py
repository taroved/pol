import MySQLdb


def get_conn(creds):
    db = MySQLdb.connect(host=creds['HOST'], port=int(creds['PORT']), user=creds['USER'], passwd=creds['PASSWORD'], db=creds['NAME'], init_command='SET NAMES utf8mb4')
    db.autocommit(True)
    return db
