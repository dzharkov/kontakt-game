from annoying.decorators import render_to
from django.http import HttpResponse
from games.models import *
from games.managers import *
from django.contrib.auth import login
from django.contrib.auth.models import User

def clear_room(request):
    ContactManager.create_dummy_contacts_for_game()
    return HttpResponse("cleared");

@render_to('room/main.html')
def room(request, id):

    user = User.objects.get(pk=id)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

    return { }
