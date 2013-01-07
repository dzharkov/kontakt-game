from functools import wraps
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.db.models import Q
import redis
from annoying.decorators import render_to
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from games.managers import *

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
    ContactManager.create_dummy_contacts_for_game()

    redis_connection = create_redis_connection()

    redis_connection.publish('web_channel', 'reload_games')

    return HttpResponse("cleared")

@render_to('room/main.html')
@login_required
def room(request, room_id):

    room = get_object_or_404(Room, pk=room_id)

    user = request.user

    if not room.has_user_access(user):
        return HttpResponseRedirect(reverse('rooms.views.list'))

    redis_connection = create_redis_connection()

    redis_connection.hset('room:' + str(room_id), request.session.session_key, user.id)

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

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)

        if form.is_valid():
            form.save(commit=False)
            room.save()
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

    room.delete()

    redis = create_redis_connection()
    redis.publish('web_channel', 'room_closed:' + str(id))

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

