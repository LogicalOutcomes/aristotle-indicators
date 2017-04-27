# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indicators', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=64)),
                ('short_name', models.CharField(max_length=64)),
                ('name', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['short_name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CategoryCombination',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=64)),
                ('short_name', models.CharField(max_length=64)),
                ('name', models.CharField(max_length=128)),
                ('categories', models.ManyToManyField(related_name='category_combination', to='indicators.Category')),
            ],
            options={
                'ordering': ['short_name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CategoryOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=64)),
                ('short_name', models.CharField(max_length=64)),
                ('name', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['short_name'],
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='category',
            name='options',
            field=models.ManyToManyField(related_name='categories', to='indicators.CategoryOption'),
        ),
    ]
