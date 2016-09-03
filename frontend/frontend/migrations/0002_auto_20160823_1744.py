# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedfield',
            name='content_type',
            field=models.CharField(default=b'text', max_length=5, choices=[(b'text', b'Text'), (b'html', b'HTML'), (b'link', b'Link'), (b'image', b'Image')]),
        ),
        migrations.AddField(
            model_name='feedfield',
            name='required',
            field=models.BooleanField(default=True),
        ),
    ]
