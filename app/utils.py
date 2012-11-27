#-*- coding: utf-8 -*-
import contextlib

from django.db import connection
from functools import wraps
from django.http import HttpResponse
from django.utils import simplejson as json

def api_response(*jargs, **jkwargs):
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            r = HttpResponse(mimetype='application/json')

            try:
                view_response = func(*args, **kwargs)
                result = { 'result' : 1, }

                if view_response and ((isinstance(view_response,dict) and len(view_response) > 0) or not isinstance(view_response,dict)):
                    result['data'] = view_response

            except Exception as e:
                result = { 'result' : 0, 'message' : e.__unicode__() }
                r.status_code = 500

            if result:
                indent = jkwargs.pop('indent', 4)
                r.write(json.dumps(result, indent=indent, **jkwargs))
            else:
                r.write("{}")
            return r
        return inner
    return outer


@contextlib.contextmanager
def acquire_table_lock(read, write):
    '''Acquire read & write locks on tables.

    Usage example:
    from polls.models import Poll, Choice
    with acquire_table_lock(read=[Poll], write=[Choice]):
        pass
    '''
    cursor = lock_table(read, write)
    try:
        yield cursor
    finally:
        unlock_table(cursor)


def lock_table(read, write):
    '''Acquire read & write locks on tables.'''
    # MySQL
    if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
        # Get the actual table names
        write_tables = [model._meta.db_table for model in write]
        write_tables.append('django_session')
        write_tables.append('auth_user')
        read_tables = [model._meta.db_table for model in read]
        # Statements
        write_statement = ', '.join(['%s WRITE' % table for table in write_tables])
        read_statement = ', '.join(['%s READ' % table for table in read_tables])
        statements = [write_statement, read_statement] if len(read) > 0 else [write_statement]
        statement = 'LOCK TABLES %s' % ', '.join(statements)
        # Acquire the lock
        cursor = connection.cursor()
        cursor.execute(statement)
        return cursor
    # Other databases: not supported
    else:
        raise Exception('This backend is not supported: %s' %
                        connection.settings_dict['ENGINE'])


def unlock_table(cursor):
    '''Release all acquired locks.'''
    # MySQL
    if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
        cursor.execute("UNLOCK TABLES")
    # Other databases: not supported
    else:
        raise Exception('This backend is not supported: %s' %
                        connection.settings_dict['ENGINE'])