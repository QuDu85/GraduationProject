# Generated by Django 3.0 on 2022-07-03 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_locked',
            field=models.BooleanField(default=False),
        ),
    ]
