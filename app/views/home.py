from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return render(request, 'app/index.html');

def about(request):
    return render(request, 'app/about.html');

def thanks(request):
    return render(request, 'app/thanks.html');