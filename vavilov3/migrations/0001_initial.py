#
# Copyright (C) 2019 P.Ziarsolo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#

# Generated by Django 2.1.7 on 2019-03-20 16:04

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import vavilov3.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
            ],
            options={
                'db_table': 'vavilov_user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
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
                ('value', models.CharField(max_length=255)),
                ('observer', models.CharField(max_length=255, null=True)),
                ('creation_time', models.DateTimeField(null=True)),
            ],
            options={
                'db_table': 'vavilov_observation',
            },
        ),
        migrations.CreateModel(
            name='ObservationImage',
            fields=[
                ('observation_image_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('observation_image_uid', models.TextField(unique=True)),
                ('image', models.ImageField(max_length=1000, upload_to=vavilov3.models.get_image_upload_path)),
                ('image_medium', models.ImageField(blank=True, max_length=1000, null=True, upload_to=vavilov3.models.get_medium_image_upload_path)),
                ('image_small', models.ImageField(blank=True, max_length=1000, null=True, upload_to=vavilov3.models.get_small_image_upload_path)),
                ('observer', models.CharField(max_length=255, null=True)),
                ('creation_time', models.DateTimeField(null=True)),
            ],
            options={
                'db_table': 'vavilov_observation_images',
            },
        ),
        migrations.CreateModel(
            name='ObservationUnit',
            fields=[
                ('observation_unit_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=255, unique=True)),
                ('level', models.CharField(db_index=True, max_length=255)),
                ('replicate', models.CharField(max_length=255, null=True)),
                ('accession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.Accession')),
            ],
            options={
                'db_table': 'vavilov_observation_unit',
            },
        ),
        migrations.CreateModel(
            name='ObservationVariable',
            fields=[
                ('observation_variable_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=255, unique=True)),
                ('description', models.CharField(max_length=255)),
                ('method', models.CharField(max_length=255)),
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
            name='Plant',
            fields=[
                ('plant_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=255, unique=True)),
                ('x', models.CharField(max_length=255, null=True)),
                ('y', models.CharField(max_length=255, null=True)),
                ('block_number', models.CharField(db_index=True, max_length=255, null=True)),
                ('entry_number', models.CharField(db_index=True, max_length=255, null=True)),
                ('plant_number', models.CharField(db_index=True, max_length=255, null=True)),
                ('plot_number', models.CharField(db_index=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'vavilov_plant',
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
            name='Scale',
            fields=[
                ('scale_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=255, unique=True)),
                ('description', models.CharField(max_length=255)),
                ('decimal_places', models.IntegerField(null=True)),
                ('max', models.FloatField(null=True)),
                ('min', models.FloatField(null=True)),
            ],
            options={
                'db_table': 'vavilov_scale',
            },
        ),
        migrations.CreateModel(
            name='ScaleCategory',
            fields=[
                ('scale_categories_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('value', models.CharField(max_length=100)),
                ('rank', models.IntegerField(null=True)),
                ('description', models.CharField(max_length=255)),
                ('scale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.Scale')),
            ],
            options={
                'db_table': 'vavilov_scale_category',
            },
        ),
        migrations.CreateModel(
            name='ScaleDataType',
            fields=[
                ('scale_data_type_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=255, unique=True)),
            ],
            options={
                'db_table': 'vavilov_observation_data_type',
            },
        ),
        migrations.CreateModel(
            name='Study',
            fields=[
                ('study_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('is_public', models.BooleanField()),
                ('is_active', models.BooleanField(null=True)),
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
            name='Trait',
            fields=[
                ('trait_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=255, unique=True)),
                ('description', models.TextField()),
                ('ontology', models.CharField(max_length=100, null=True)),
                ('ontology_id', models.CharField(max_length=100, null=True)),
            ],
            options={
                'db_table': 'vavilov_trait',
            },
        ),
        migrations.CreateModel(
            name='UserTasks',
            fields=[
                ('user_task_id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('task_id', models.CharField(max_length=100)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'vavilov_user_task',
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
        migrations.AlterUniqueTogether(
            name='trait',
            unique_together={('ontology', 'ontology_id')},
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
            model_name='scale',
            name='data_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.ScaleDataType'),
        ),
        migrations.AddField(
            model_name='scale',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Group'),
        ),
        migrations.AddField(
            model_name='project',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Group'),
        ),
        migrations.AddField(
            model_name='plant',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Group'),
        ),
        migrations.AddField(
            model_name='plant',
            name='observation_units',
            field=models.ManyToManyField(to='vavilov3.ObservationUnit'),
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
            model_name='observationvariable',
            name='scale',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Scale'),
        ),
        migrations.AddField(
            model_name='observationvariable',
            name='trait',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3.Trait'),
        ),
        migrations.AddField(
            model_name='observationunit',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.Study'),
        ),
        migrations.AddField(
            model_name='observationimage',
            name='observation_unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3.ObservationUnit'),
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
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
        migrations.AlterUniqueTogether(
            name='taxon',
            unique_together={('name', 'rank')},
        ),
        migrations.AlterUniqueTogether(
            name='scalecategory',
            unique_together={('scale', 'value'), ('scale', 'description'), ('scale', 'rank')},
        ),
        migrations.AlterUniqueTogether(
            name='passport',
            unique_together={('institute', 'germplasm_number', 'data_source')},
        ),
        migrations.AlterUniqueTogether(
            name='observationvariable',
            unique_together={('trait', 'method', 'scale')},
        ),
        migrations.AlterUniqueTogether(
            name='observation',
            unique_together={('observation_variable', 'observation_unit', 'value', 'observer', 'creation_time')},
        ),
        migrations.AlterUniqueTogether(
            name='accession',
            unique_together={('institute', 'germplasm_number')},
        ),
    ]
