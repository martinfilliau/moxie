import logging

from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)


db = SQLAlchemy()


class DBHealthcheck(object):

    def healthcheck(self):
        try:
            connection = db.engine.connect()
            # doing a simple SQL query "SELECT 1" on the configured database
            result = connection.execute("SELECT 1;")
            # attempting to retrieve the first line of the result... or None
            result.first()
            connection.close()
            return True, 'OK'
        except Exception as e:
            logger.error('Error while checking health of DB', exc_info=True)
            return False, e
