from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from app.forms import RegistrationForm

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

def login(request, template='app/about.html'):
	return render(request, template);