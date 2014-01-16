from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class DBHealthcheck(object):

    def healthcheck(self):
        try:
            connection = db.engine.connect()
            result = connection.execute("SELECT 1;")
            result.first()
            connection.close()
            return True, 'OK'
        except Exception as e:
            return False, e
