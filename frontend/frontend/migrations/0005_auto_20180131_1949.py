# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0004_feed_edited'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postfield',
            name='field',
        ),
        migrations.RemoveField(
            model_name='postfield',
            name='post',
        ),
        migrations.DeleteModel(
            name='PostField',
        ),
    ]
