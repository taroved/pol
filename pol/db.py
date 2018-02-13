import MySQLdb
import MySQLdb.cursors


def get_conn(creds, dict_result=False):
    cursor = MySQLdb.cursors.DictCursor if dict_result else MySQLdb.cursors.Cursor
    db = MySQLdb.connect(host=creds['HOST'], port=int(creds['PORT']), user=creds['USER'], passwd=creds['PASSWORD'],
                         db=creds['NAME'], init_command='SET NAMES utf8mb4', cursorclass=cursor)
    db.autocommit(True)
    return db
