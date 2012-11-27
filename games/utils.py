from functools import wraps
from models import Contact,Game
from django.db import transaction

from app.utils import acquire_table_lock

def contacts_lock(func):
    @wraps(func)
    def inner(*args, **kwargs):
        transaction.enter_transaction_management(True)
        with acquire_table_lock(write=[Contact,Game],read=[]):
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                transaction.rollback()
                raise e
            transaction.commit()

            return result
    return inner