# Generated by Django 2.2.10 on 2020-03-25 15:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vavilov3', '0003_auto_20200306_1107'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeedPetition',
            fields=[
                ('petition_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('petitioner_name', models.CharField(max_length=100)),
                ('petitioner_type', models.CharField(max_length=100)),
                ('petitioner_institution', models.CharField(max_length=100)),
                ('petitioner_address', models.CharField(max_length=255)),
                ('petitioner_city', models.CharField(max_length=100)),
                ('petitioner_postal_code', models.CharField(max_length=10)),
                ('petitioner_region', models.CharField(max_length=100)),
                ('petitioner_email', models.EmailField(max_length=254)),
                ('petition_date', models.DateField()),
                ('petition_aim', models.TextField()),
                ('petition_comments', models.TextField(null=True)),
                ('petitioner_country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Country')),
                ('requested_accessions', models.ManyToManyField(to='vavilov3.Accession')),
            ],
            options={
                'db_table': 'vavilov_seed_petition',
            },
        ),
    ]
