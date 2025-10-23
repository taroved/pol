# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0008_auto_20180215_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='name',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
    ]

