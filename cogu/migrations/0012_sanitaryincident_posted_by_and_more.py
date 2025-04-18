# Generated by Django 4.2.20 on 2025-04-12 19:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cogu', '0011_alter_incidentmedia_downloaded_file_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sanitaryincident',
            name='posted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='postedby', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='sanitaryincident',
            name='validated_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='employeeuser',
            name='roleemployee',
            field=models.CharField(choices=[('National', 'National'), ('Regional', 'Régional'), ('DistrictSanitaire', 'District Sanitaire'), ('Centre', 'Centre de Sante'), ('Public', 'Utilisateur Publique')], default='Public', max_length=20),
        ),
    ]
