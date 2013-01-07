import tornado.database
import tornadoredis
import redis

import threading, Queue

from app import settings

class AsyncDatabaseModifier():
    def __init__(self, pool_size=1):
        self._threads = []
        self._tasks = Queue.Queue()
        # create threads
        for i in xrange(pool_size):
            t = DbWorker(self)
            t.daemon = True
            t.start()
            self._threads.append(t)
    def execute(self, query, *argv):
        self._tasks.put([query, argv])

class DbWorker(threading.Thread):
    def __init__(self, cnt):
        self._controller = cnt
        self._db = tornado.database.Connection('localhost', settings.DATABASES['default']['NAME'], settings.DATABASES['default']['USER'], settings.DATABASES['default']['PASSWORD'])
        super(DbWorker, self).__init__()
    def run(self):
        cnt = self._controller

        while True:
            task = cnt._tasks.get(True)
            self._db.execute(task[0], *task[1])

db = tornado.database.Connection('localhost', settings.DATABASES['default']['NAME'], settings.DATABASES['default']['USER'], settings.DATABASES['default']['PASSWORD'])
redis_connection = redis.Redis(host=settings.REDIS_HOST, db=settings.REDIS_DB)
redis_subscriptions = tornadoredis.Client(host=settings.REDIS_HOST, selected_db=settings.REDIS_DB)

db_modifier = AsyncDatabaseModifier()
