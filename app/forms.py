# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.models import User

class RegistrationForm(forms.Form):
	username = forms.CharField(label="Имя пользователя", max_length=100)
	email    = forms.EmailField(label="Электронная почта", max_length=100)
	password = forms.CharField(widget=forms.PasswordInput, 
		label="Пароль", 
		min_length=6, 
		max_length=20)
	password_confirm = forms.CharField(widget=forms.PasswordInput, 
		label="Подтверждение пароля",
		min_length=6, 
		max_length=20)
	
	def clean(self,*args, **kwargs):
		if self.data['password'] != self.data['password_confirm']:
			raise forms.ValidationError('Passwords are not the same')
		if User.objects.filter(username=self.data['username']).count()>0:
			raise forms.ValidationError('A user with such username already exists')
		if User.objects.filter(email=self.data['email']).count()>0:
			raise forms.ValidationError('A user with such email already exists')
		return super(RegistrationForm, self).clean(*args, **kwargs)

class LoginForm(forms.Form):
    login = forms.CharField(label="Логин", max_length=100)
    password = forms.CharField(widget=forms.PasswordInput,label="Пароль")


class EmptyForm(forms.Form): pass