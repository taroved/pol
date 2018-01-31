from django.db import models

class Feed(models.Model):
    uri = models.CharField(max_length=2000)
    xpath = models.CharField(max_length=2000)
    edited = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

class Field(models.Model):
    name = models.CharField(max_length=200)
    required = models.BooleanField(default=True)

class FeedField(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    xpath = models.CharField(max_length=2000)

class Post(models.Model):
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    md5sum = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = ['feed', 'md5sum']
