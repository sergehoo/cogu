# Generated by Django 4.2.20 on 2025-04-16 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cogu', '0017_whatsappmessage_read'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employeeuser',
            name='photo',
            field=models.ImageField(blank=True, default='users/images/user.webp', null=True, upload_to='users/images/'),
        ),
    ]
