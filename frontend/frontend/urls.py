"""frontend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin

from . import views

urlpatterns = i18n_patterns(
    url(r'^$', views.index, name='index'),
    url(r'^setup$', views.setup, name='setup'),
    url(r'^preview/([0-9]+)$', views.preview, name='preview'),
    url(r'^contact$', views.contact, name='contact'),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns.append(url(r'^setup_get_selected_ids$', views.setup_get_selected_ids, name='setup_get_selected_ids'))
urlpatterns.append(url(r'^setup_create_feed$', views.setup_create_feed, name='setup_create_feed'))
urlpatterns.append(url(r'^setup_create_feed_ext$', views.setup_create_feed_ext, name='setup_create_feed_ext'))
urlpatterns.append(url(r'^setup_validate_selectors$', views.setup_validate_selectors, name='setup_validate_selectors'))
