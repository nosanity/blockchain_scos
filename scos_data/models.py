# coding: utf-8

from django.db import models
from jsonfield import JSONField


class RawJsonData(models.Model):
    data = JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
