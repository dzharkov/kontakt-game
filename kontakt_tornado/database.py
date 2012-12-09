import tornado.database
import tornadoredis
import redis

from app import settings

db = tornado.database.Connection('localhost', settings.DATABASES['default']['NAME'], settings.DATABASES['default']['USER'], settings.DATABASES['default']['PASSWORD'])
redis_connection = redis.Redis(host=settings.REDIS_HOST, db=settings.REDIS_DB)
redis_subscriptions = tornadoredis.Client(host=settings.REDIS_HOST, selected_db=settings.REDIS_DB)
