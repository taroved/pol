# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('md5sum', models.CharField(max_length=32)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PostField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(max_length=65535)),
                ('field', models.ForeignKey(to='frontend.Field')),
                ('post', models.ForeignKey(to='frontend.Post')),
            ],
        ),
        migrations.AddField(
            model_name='feed',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2017, 7, 11, 21, 19, 23, 580569), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='post',
            name='feed',
            field=models.ForeignKey(to='frontend.Feed'),
        ),
        migrations.AlterIndexTogether(
            name='post',
            index_together=set([('feed', 'md5sum')]),
        ),
    ]
