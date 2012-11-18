from django.http import HttpResponse
from django.shortcuts import render

def index(request, template='app/index.html'):
    return render(request, template);

def about(request, template='app/about.html'):
    return render(request, template);