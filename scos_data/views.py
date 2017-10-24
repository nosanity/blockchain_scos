# coding: utf-8

from django.views.generic import TemplateView


class Frontage(TemplateView):
    template_name = 'frontpage.html'
