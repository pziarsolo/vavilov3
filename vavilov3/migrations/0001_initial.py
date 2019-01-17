# Generated by Django 2.1.4 on 2019-01-16 15:21

import django.contrib.auth.models
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accession',
            fields=[
                ('accession_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('is_public', models.BooleanField()),
                ('germplasm_number', models.CharField(db_index=True, max_length=100)),
                ('is_available', models.NullBooleanField()),
                ('conservation_status', models.CharField(max_length=50, null=True)),
                ('is_save_duplicate', models.NullBooleanField()),
                ('data', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={
                'db_table': 'vavilov_accession',
            },
        ),
        migrations.CreateModel(
            name='AccessionSet',
            fields=[
                ('accessionset_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('is_public', models.BooleanField()),
                ('accessionset_number', models.CharField(db_index=True, max_length=100, null=True, unique=True)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField()),
                ('accessions', models.ManyToManyField(to='vavilov3.Accession')),
            ],
            options={
                'db_table': 'vavilov_accessionset',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('country_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, max_length=4, unique=True)),
                ('name', models.CharField(db_index=True, max_length=255, unique=True)),
            ],
            options={
                'db_table': 'vavilov_country',
            },
        ),
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('data_source_id', models.AutoField(primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, max_length=20, unique=True)),
                ('kind', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'vavilov_data_source',
            },
        ),
        migrations.CreateModel(
            name='Institute',
            fields=[
                ('institute_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, max_length=20, unique=True)),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={
                'db_table': 'vavilov_institute',
            },
        ),
        migrations.CreateModel(
            name='Observation',
            fields=[
                ('observation_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('observationTimeStamp', models.DateField()),
                ('observer', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='ObservationDataType',
            fields=[
                ('observation_data_type_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=255, unique=True)),
            ],
            options={
                'db_table': 'vavilov_observation_data_type',
            },
        ),
        migrations.CreateModel(
            name='ObservationUnit',
            fields=[
                ('observation_unit_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('level', models.CharField(max_length=255)),
                ('replicate', models.CharField(max_length=255)),
                ('accession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.Accession')),
            ],
        ),
        migrations.CreateModel(
            name='ObservationVariable',
            fields=[
                ('observation_variable_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=255, unique=True)),
                ('trait', models.CharField(db_index=True, max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('method', models.CharField(max_length=255)),
                ('unit', models.CharField(blank=True, max_length=255, null=True)),
                ('data_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.ObservationDataType')),
            ],
            options={
                'db_table': 'vavilov_observation_variable',
            },
        ),
        migrations.CreateModel(
            name='Passport',
            fields=[
                ('passport_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField()),
                ('germplasm_number', models.CharField(db_index=True, max_length=100)),
                ('collection_number', models.CharField(db_index=True, max_length=255, null=True)),
                ('accession_name', models.CharField(db_index=True, max_length=255, null=True)),
                ('crop_name', models.CharField(db_index=True, max_length=255, null=True)),
                ('state', models.CharField(db_index=True, max_length=255, null=True)),
                ('province', models.CharField(db_index=True, max_length=255, null=True)),
                ('municipality', models.CharField(db_index=True, max_length=255, null=True)),
                ('location_site', models.TextField(db_index=True, null=True)),
                ('biological_status', models.CharField(db_index=True, max_length=3, null=True)),
                ('collection_source', models.CharField(db_index=True, max_length=3, null=True)),
                ('latitude', models.DecimalField(decimal_places=4, max_digits=9, null=True)),
                ('longitude', models.DecimalField(decimal_places=4, max_digits=9, null=True)),
                ('pdci', models.DecimalField(decimal_places=2, max_digits=4, null=True)),
                ('accession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passports', to='vavilov3.Accession')),
                ('collecting_institute', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='passport_collecting_institute', to='vavilov3.Institute')),
                ('country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Country')),
                ('data_source', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.DataSource')),
                ('institute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passport_institute', to='vavilov3.Institute')),
            ],
            options={
                'db_table': 'vavilov_passport',
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('project_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('is_public', models.BooleanField()),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('active', models.BooleanField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
            options={
                'db_table': 'vavilov_project',
            },
        ),
        migrations.CreateModel(
            name='Rank',
            fields=[
                ('rank_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('level', models.IntegerField()),
            ],
            options={
                'db_table': 'vavilov_rank',
            },
        ),
        migrations.CreateModel(
            name='Study',
            fields=[
                ('study_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('is_public', models.BooleanField()),
                ('is_active', models.BooleanField()),
                ('name', models.CharField(db_index=True, max_length=255, unique=True)),
                ('description', models.CharField(max_length=255)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={
                'db_table': 'vavilov_study',
            },
        ),
        migrations.CreateModel(
            name='Taxon',
            fields=[
                ('taxon_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('rank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.Rank')),
            ],
            options={
                'db_table': 'vavilov_taxon',
            },
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('auth.group',),
            managers=[
                ('objects', django.contrib.auth.models.GroupManager()),
            ],
        ),
        migrations.AddField(
            model_name='study',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Group'),
        ),
        migrations.AddField(
            model_name='study',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Project'),
        ),
        migrations.AddField(
            model_name='project',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Group'),
        ),
        migrations.AddField(
            model_name='passport',
            name='taxa',
            field=models.ManyToManyField(to='vavilov3.Taxon'),
        ),
        migrations.AddField(
            model_name='observationvariable',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Group'),
        ),
        migrations.AddField(
            model_name='observationunit',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.Study'),
        ),
        migrations.AddField(
            model_name='observation',
            name='observation_unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.ObservationUnit'),
        ),
        migrations.AddField(
            model_name='observation',
            name='observation_variable',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.ObservationVariable'),
        ),
        migrations.AddField(
            model_name='accessionset',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Group'),
        ),
        migrations.AddField(
            model_name='accessionset',
            name='institute',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.Institute'),
        ),
        migrations.AddField(
            model_name='accession',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Group'),
        ),
        migrations.AddField(
            model_name='accession',
            name='institute',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.Institute'),
        ),
        migrations.AlterUniqueTogether(
            name='taxon',
            unique_together={('name', 'rank')},
        ),
        migrations.AlterUniqueTogether(
            name='passport',
            unique_together={('institute', 'germplasm_number', 'data_source')},
        ),
        migrations.AlterUniqueTogether(
            name='observationvariable',
            unique_together={('name', 'method', 'data_type', 'unit')},
        ),
        migrations.AlterUniqueTogether(
            name='accession',
            unique_together={('institute', 'germplasm_number')},
        ),
    ]