# Generated by Django 5.1.6 on 2025-02-25 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('survivor', 'Survivor'), ('officer', 'SGBV Officer'), ('law_enforcement', 'Law Enforcement'), ('medical_officer', 'Medical Officer')], default='survivor', max_length=20),
        ),
    ]
