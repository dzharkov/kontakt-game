import redis
from annoying.decorators import render_to
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from games.managers import *

from forms import RoomForm
from models import Room

from app import settings

def clear_room(request):
    ContactManager.create_dummy_contacts_for_game()

    redis_connection = redis.Redis(host=settings.REDIS_HOST, db=settings.REDIS_DB)

    redis_connection.publish('reload', 'games')

    return HttpResponse("cleared")

@render_to('room/main.html')
@login_required
def room(request, room_id):

    room = get_object_or_404(Room, pk=room_id)

    user = request.user

    redis_connection = redis.Redis(host=settings.REDIS_HOST, db=settings.REDIS_DB)

    redis_connection.hset('room:' + str(room_id), request.session.session_key, user.id)

    return { 'room_id' : int(room_id) }

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
def edit(request, id):
    room = get_object_or_404(Room, pk=id)

    if request.user != room.owner:
        return HttpResponse(status=403)

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)

        if form.is_valid():
            form.save(commit=False)
            room.save()
            return HttpResponseRedirect(request.get_full_path())
    else:
        form = RoomForm(instance=room)

    return { 'form' : form }

@render_to('room/list.html')
@login_required
def list(request):
    rooms = Room.objects.order_by('-online_amount').all()
    return { 'rooms' : rooms }

@render_to('room/my_list.html')
@login_required
def my_list(request):
    rooms = Room.objects.filter(owner=request.user).all()
    return { 'rooms' : rooms }

