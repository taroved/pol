# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0003_field_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='edited',
            field=models.BooleanField(default=False),
        ),
    ]
