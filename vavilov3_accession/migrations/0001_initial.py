# Generated by Django 2.1.3 on 2018-11-26 14:23

import django.contrib.auth.models
import django.contrib.auth.validators
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


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
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
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
                ('accessions', models.ManyToManyField(to='vavilov3_accession.Accession')),
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
                ('accession', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passports', to='vavilov3_accession.Accession')),
                ('collecting_institute', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='passport_collecting_institute', to='vavilov3_accession.Institute')),
                ('country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3_accession.Country')),
                ('data_source', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3_accession.DataSource')),
                ('institute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passport_institute', to='vavilov3_accession.Institute')),
            ],
            options={
                'db_table': 'vavilov_passport',
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
            name='Taxon',
            fields=[
                ('taxon_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('rank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3_accession.Rank')),
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
            model_name='passport',
            name='taxa',
            field=models.ManyToManyField(to='vavilov3_accession.Taxon'),
        ),
        migrations.AddField(
            model_name='accessionset',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3_accession.Group'),
        ),
        migrations.AddField(
            model_name='accessionset',
            name='institute',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3_accession.Institute'),
        ),
        migrations.AddField(
            model_name='accession',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vavilov3_accession.Group'),
        ),
        migrations.AddField(
            model_name='accession',
            name='institute',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vavilov3_accession.Institute'),
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
            name='passport',
            unique_together={('institute', 'germplasm_number', 'data_source')},
        ),
        migrations.AlterUniqueTogether(
            name='accession',
            unique_together={('institute', 'germplasm_number')},
        ),
    ]
