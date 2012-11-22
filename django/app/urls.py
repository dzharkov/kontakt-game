from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'app.views.home.index'),
    url(r'^room/', include('rooms.urls')),
    url(r'^account/register$', 'app.views.account.register'),
    url(r'^account/login$', 'app.views.account.login'),
    url(r'^about$', 'app.views.home.about'),
    url(r'^thanks$', 'app.views.home.thanks'),
    # url(r'^app/', include('app.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
