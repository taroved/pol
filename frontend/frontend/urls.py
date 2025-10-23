"""frontend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.urls import path, re_path
from django.contrib import admin

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('setup', views.setup, name='setup'),
    re_path(r'^preview/([0-9]+)$', views.preview, name='preview'),
    path('feeds', views.feeds, name='feeds'),
    path('contact', views.contact, name='contact'),
    path('admin/', admin.site.urls),
    path('setup_get_selected_ids', views.setup_get_selected_ids, name='setup_get_selected_ids'),
    path('setup_create_feed', views.setup_create_feed, name='setup_create_feed'),
    path('setup_create_feed_ext', views.setup_create_feed_ext, name='setup_create_feed_ext'),
    path('setup_validate_selectors', views.setup_validate_selectors, name='setup_validate_selectors'),
    re_path(r'^downloader', views.downloader_proxy, name='downloader_proxy'),
    re_path(r'^feed/(\d+)$', views.feed_proxy, name='feed_proxy'),
]
