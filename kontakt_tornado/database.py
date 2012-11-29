import tornado.database
import tornadoredis

from app import settings

db = tornado.database.Connection('localhost', settings.DATABASES['default']['NAME'], settings.DATABASES['default']['USER'], settings.DATABASES['default']['PASSWORD'])
redis = tornadoredis.Client(host=settings.REDIS_HOST, selected_db=settings.REDIS_DB)
