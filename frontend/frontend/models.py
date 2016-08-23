from django.db import models


class Feed(models.Model):
    uri = models.CharField(max_length=2000)
    xpath = models.CharField(max_length=2000)

class Field(models.Model):
    name = models.CharField(max_length=200)

class FeedField(models.Model):
    CT_TEXT = 'text'
    CT_HTML = 'html'
    CT_LINK = 'link'
    CT_IMAGE = 'image'

    CONTENT_TYPE_CHOICES = (
        (CT_TEXT, 'Text'),
        (CT_HTML, 'HTML'),
        (CT_LINK, 'Link'),
        (CT_IMAGE, 'Image'),
    )

    feed = models.ForeignKey(Feed, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    xpath = models.CharField(max_length=2000)
    content_type = models.CharField(
        max_length=5,
        choices=CONTENT_TYPE_CHOICES,
        default=CT_TEXT,
    )
    required = models.BooleanField(default=True)
