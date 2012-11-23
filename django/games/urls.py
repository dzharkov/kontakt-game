from django.conf.urls import patterns, include, url

urlpatterns = patterns('games.views',
    url(r'^accept_contact/(?P<id>\d+)$', 'accept_contact'),
)
