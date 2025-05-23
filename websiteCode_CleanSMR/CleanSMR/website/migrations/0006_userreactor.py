# Generated by Django 5.1.4 on 2024-12-11 23:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_alter_reactor_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserReactor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('reactor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.reactor')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
