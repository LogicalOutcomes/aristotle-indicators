# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0002_auto_20170427_1340'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='collection',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='categorycombination',
            name='collection',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='categoryoption',
            name='collection',
            field=models.CharField(default='', max_length=64),
            preserve_default=False,
        ),
    ]
