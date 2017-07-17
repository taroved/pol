# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0002_auto_20170711_2119'),
    ]

    operations = [
        migrations.AddField(
            model_name='field',
            name='required',
            field=models.BooleanField(default=True),
        ),
    ]
