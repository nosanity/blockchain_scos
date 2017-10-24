# coding: utf-8

from django.conf.urls import url
from django.contrib.auth.views import LogoutView, LoginView
from . import views


urlpatterns = (
    url(r'^$', views.Frontage.as_view(), name='frontpage'),
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='log-out'),
)
