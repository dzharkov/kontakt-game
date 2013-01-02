from annoying.decorators import render_to
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login, logout
from app.forms import RegistrationForm, LoginForm

def register(request):
	if request.method=='POST':
		form = RegistrationForm(request.POST)
		if form.is_valid():
			new_user = User()
			new_user.username = form.cleaned_data['username']
			new_user.set_password(form.cleaned_data['password'])
			new_user.email = form.cleaned_data['email']
			new_user.save()
			return HttpResponseRedirect('/thanks')
	else:
		form = RegistrationForm()
	return render(request, 'app/register.html', {'form': form});

@render_to('app/login.html')
def login_view(request):
    bad_attempt = False
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['login']
            password = form.cleaned_data['password']
            user = authenticate(username=username,password=password)
            if user:
                login(request, user)
                return HttpResponseRedirect(reverse('rooms.views.list'))
            else:
                bad_attempt = True
    else:
        form = LoginForm()
    return { 'form' : form, 'bad_attempt' : bad_attempt }

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')
