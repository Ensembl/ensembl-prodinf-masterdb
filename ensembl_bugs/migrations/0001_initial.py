# Generated by Django 2.2.7 on 2019-11-20 11:59

from django.db import migrations, models
import fernet_fields.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Credentials',
            fields=[
                ('cred_id', models.AutoField(primary_key=True, serialize=False)),
                ('cred_name', models.CharField(max_length=150, unique=True, verbose_name='Name')),
                ('cred_url', models.CharField(max_length=255, verbose_name='Access Url')),
                ('user', models.CharField(max_length=100, verbose_name='Jira User Name')),
                ('credentials', fernet_fields.fields.EncryptedCharField(max_length=255, verbose_name='Jira Password')),
            ],
        ),
    ]
