from django.db import models


class Feed(models.Model):
    uri = models.CharField(max_length=2000)
    xpath = models.CharField(max_length=2000)

class Field(models.Model):
    name = models.CharField(max_length=200)

class FeedField(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    xpath = models.CharField(max_length=2000)
