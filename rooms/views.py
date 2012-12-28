import redis
from annoying.decorators import render_to
from django.http import HttpResponse
from games.managers import *
from django.contrib.auth import login
from django.contrib.auth.models import User

from app import settings

def clear_room(request):
    ContactManager.create_dummy_contacts_for_game()

    redis_connection = redis.Redis(host=settings.REDIS_HOST, db=settings.REDIS_DB)

    redis_connection.publish('reload', 'games')

    return HttpResponse("cleared");

@render_to('room/main.html')
def room(request, room_id, user_id):

    user = User.objects.get(pk=user_id)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

    redis_connection = redis.Redis(host=settings.REDIS_HOST, db=settings.REDIS_DB)

    redis_connection.hset('room:' + str(room_id), request.session.session_key, user.id)

    return { 'room_id' : int(room_id) }
