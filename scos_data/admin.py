# coding: utf-8

from django.contrib import admin
from .models import RawJsonData


@admin.register(RawJsonData)
class RawJsonDataAdmin(admin.ModelAdmin):
    pass
