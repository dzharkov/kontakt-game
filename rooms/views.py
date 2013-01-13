# -*- coding: utf-8 -*-
from functools import wraps
import redis
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from annoying.decorators import render_to

from forms import RoomForm
from models import Room

from app import settings

def create_redis_connection():
    return redis.Redis(host=settings.REDIS_HOST, db=settings.REDIS_DB)

def room_edit(func):
    @wraps(func)
    def inner(*args, **kwargs):
        request = args[0]
        room = get_object_or_404(Room, pk=kwargs['id'])
        del kwargs['id']

        if room.owner != request.user:
            return HttpResponseForbidden()

        kwargs['room'] = room

        return func(*args, **kwargs)
    return inner

def clear_room(request):
    from django.db import connection, transaction

    cursor = connection.cursor()
    transaction.enter_transaction_management(True)
    try:
        cursor.execute("SET foreign_key_checks = 0")
        cursor.execute("TRUNCATE games_contact")
        cursor.execute("TRUNCATE games_game")
        cursor.execute("TRUNCATE rooms_room")
        cursor.execute("TRUNCATE rooms_room_invited")
        cursor.execute("SET foreign_key_checks = 1")

        cursor.execute(u"INSERT INTO `rooms_room` VALUES (1,'Любители моделей', 2, 0, 0)")
        cursor.execute(u"INSERT INTO `rooms_room` VALUES (2,'Экзистенциальная Россия', 2, 0, 0)")

        cursor.execute(u"INSERT INTO `games_game` VALUES (1,2,'моделирование',2,1,'running')")
        cursor.execute(u"INSERT INTO `games_game` VALUES (2,2,'прустота',8,2,'complete')")
        cursor.execute(u"INSERT INTO `games_contact` VALUES (1,1,'2012-11-22 16:56:25',3,'мода','как сказала Коко Шанель, она выходит сама из себя',NULL,NULL,NULL,1,0),(2,1,'2012-11-22 17:09:04',4,'моделирование','Оно бывает имитационным, эволюционным, и изредка даже психологическим',NULL,NULL,NULL,1,0)")
    except Exception:
        transaction.rollback()
        return HttpResponse('bad')
    transaction.commit()

    redis_connection = create_redis_connection()

    redis_connection.publish('web_channel', 'reload_games')

    return HttpResponse("cleared")

def redis_room_key(room_id):
    return 'room:' + str(room_id)

@render_to('room/main.html')
@login_required
def room(request, room_id):

    room = get_object_or_404(Room, pk=room_id)

    user = request.user

    if not room.has_user_access(user):
        return HttpResponseRedirect(reverse('rooms.views.list'))

    redis_connection = create_redis_connection()

    redis_connection.hset(redis_room_key(room_id), request.session.session_key, user.id)
    redis_connection.set('session_key:' + str(user.id), request.session.session_key)

    return { 'room' : room }

def authorize_user_and_redirect_to_room(request, room_id, user_id):
    user = User.objects.get(pk=user_id)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

    return HttpResponseRedirect(reverse('rooms.views.room', args=[room_id]))

@render_to('room/create.html')
@login_required
def create(request):

    if request.method == 'POST':
        form = RoomForm(request.POST)

        if form.is_valid():
            room = form.save(commit=False)
            room.owner = request.user
            room.save()
            url = reverse('rooms.views.edit', args=[room.id])
            return HttpResponseRedirect(url)
    else:
        form = RoomForm()

    return { 'form' : form }

@render_to('room/edit.html')
@login_required
@room_edit
def edit(request, room):
    was_private = room.is_private

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)

        if form.is_valid():
            form.save(commit=False)
            room.save()

            if room.is_private and not was_private:
                redis = create_redis_connection()
                redis.publish('web_channel', 'room_private:' + str(room.id))
                redis.hdel(redis_room_key(room.id), *redis.hkeys(redis_room_key(room.id)))

            return HttpResponseRedirect(request.get_full_path())
    else:
        form = RoomForm(instance=room)

    response_data = { 'form' : form }

    if room.is_private:
        response_data['invited_users'] = room.invited.order_by('username').all()
        response_data['users'] = User.objects.exclude(pk=room.owner.id).exclude(rooms__pk=room.id).order_by('username').all()

    return response_data

@csrf_protect
@login_required
@require_POST
@room_edit
def delete(request, room):

    redis = create_redis_connection()
    redis.publish('web_channel', 'room_deleted:' + str(room.id))
    redis.hdel(redis_room_key(room.id), *redis.hkeys(redis_room_key(room.id)))

    room.delete()

    return HttpResponseRedirect(reverse('rooms.views.my_list'))

@csrf_protect
@login_required
@require_POST
@room_edit
def add_invite(request, room, user_id):
    if room.is_private:
        user = get_object_or_404(User, pk=user_id)

        room.invited.add(user)

    return HttpResponseRedirect(reverse('rooms.views.edit', args=[room.id]))

@csrf_protect
@login_required
@require_POST
@room_edit
def delete_invite(request, room, user_id):
    if room.is_private:
        user = get_object_or_404(User, pk=user_id)

        redis = create_redis_connection()
        redis.publish('web_channel', 'kick_user_from_room:' + str(room.id) + ':' + str(user.id))
        session_key = redis.get('session_key:' + str(user.id))
        redis.hdel(redis_room_key(room.id), session_key)

        room.invited.remove(user)

    return HttpResponseRedirect(reverse('rooms.views.edit', args=[room.id]))

@render_to('room/list.html')
@login_required
def list(request):
    rooms = Room.objects.filter(
        Q(is_private=False) | Q(owner__pk=request.user.id) | Q (invited__pk=request.user.id)
    ).distinct().order_by('-online_amount').all()
    return { 'rooms' : rooms }

@render_to('room/my_list.html')
@login_required
def my_list(request):
    rooms = Room.objects.filter(owner=request.user).all()
    return { 'rooms' : rooms }

