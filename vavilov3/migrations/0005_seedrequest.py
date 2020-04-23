# Generated by Django 2.2.11 on 2020-04-06 14:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vavilov3', '0004_auto_20200402_0840'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeedRequest',
            fields=[
                ('seed_request_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('request_uid', models.CharField(db_index=True, max_length=100, unique=True)),
                ('requester_name', models.CharField(max_length=100)),
                ('requester_type', models.CharField(max_length=100)),
                ('requester_institution', models.CharField(max_length=100)),
                ('requester_address', models.CharField(max_length=255)),
                ('requester_city', models.CharField(max_length=100)),
                ('requester_postal_code', models.CharField(max_length=10)),
                ('requester_region', models.CharField(max_length=100)),
                ('requester_email', models.EmailField(max_length=254)),
                ('request_date', models.DateField()),
                ('request_aim', models.TextField()),
                ('request_comments', models.TextField(null=True)),
                ('requested_accessions', models.ManyToManyField(to='vavilov3.Accession')),
                ('requester_country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Country')),
            ],
            options={
                'db_table': 'vavilov_seed_request',
            },
        ),
    ]