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

import io
from operator import itemgetter
from os.path import join, splitext, split

from numpy import histogram
from PIL import Image

from django.db import models, connection
from django.contrib.auth.models import Group as DjangoGroup, AbstractUser
from django.contrib.postgres.fields.jsonb import JSONField
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf.global_settings import MEDIA_ROOT

from vavilov3.raw_stat_sql_commands import (get_institute_stats_raw_sql,
                                            get_country_stats_raw_sql)
from vavilov3.entities.tags import NOMINAL, ORDINAL
from vavilov3.conf.settings import PHENO_IMAGE_DIR


class User(AbstractUser):

    class Meta:
        db_table = "vavilov_user"


class UserTasks(models.Model):
    user_task_id = models.AutoField(primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=100)

    class Meta:

        db_table = 'vavilov_user_task'


class Group(DjangoGroup):

    class Meta:
        proxy = True

    @property
    def users(self):
        return self.user_set.all()


class Institute(models.Model):
    institute_id = models.AutoField(primary_key=True, editable=False)
    code = models.CharField(max_length=20, db_index=True, unique=True)
    name = models.CharField(max_length=255, db_index=True)
    data = JSONField()

    class Meta:
        db_table = 'vavilov_institute'

    def __str__(self):
        return '{}({})'.format(self.name, self.code)

    @property
    def num_accessions(self):
        return Accession.objects.filter(institute=self).count()

    @property
    def num_accessionsets(self):
        return AccessionSet.objects.filter(institute=self).count()

    def stats_by_country(self, user=None):
        stats = {}
        accession_stats = Country.objects.raw(
            get_institute_stats_raw_sql(institute_id=self.institute_id,
                                        stats_type='country',
                                        entity_type='accession',
                                        user=user))

        accessionset_stats = Country.objects.raw(
            get_institute_stats_raw_sql(institute_id=self.institute_id,
                                        stats_type='country',
                                        entity_type='accessionset',
                                        user=user))

        for row in accession_stats:
            _integrate_country_stats(stats, row, 'accession')
        for row in accessionset_stats:
            _integrate_country_stats(stats, row, 'accessionset')
        return sorted(stats.values(), key=itemgetter('num_accessions'),
                      reverse=True)

    def stats_by_taxa(self, user=None):
        stats = {}
        accession_stats = Taxon.objects.raw(
            get_institute_stats_raw_sql(institute_id=self.institute_id,
                                        stats_type='taxa',
                                        entity_type='accession',
                                        user=user))
        accessionset_stats = Taxon.objects.raw(
            get_institute_stats_raw_sql(institute_id=self.institute_id,
                                        stats_type='taxa',
                                        entity_type='accessionset',
                                        user=user))
        for row in accession_stats:
            _integrate_taxa_stats(stats, row, 'accession')
        for row in accessionset_stats:
            _integrate_taxa_stats(stats, row, 'accessionset')
        return stats

    @property
    def pdcis(self):
        pdcis = [float(p['pdci']) for p in Passport.objects.filter(institute=self).values('pdci')]
        return pdci_distrib(pdcis)


def pdci_distrib(pdcis):
        range_ = {}
        for i in range(10):
            range_[(i, i + 0.5)] = []
            range_[(i + 0.5, i + 1)] = []

        hist, bin_edges = histogram(pdcis, bins=20, range=(0, 10))
        return zip(bin_edges, hist)


def _integrate_country_stats(stats, query_stats, entity_type):
    counts = query_stats.counts
    code = query_stats.code
    name = query_stats.name

    if counts:
        if code not in stats:
            stats[code] = {'code': code, 'name': name,
                           'num_accessions': 0, 'num_accessionsets': 0}

        stats[code]['num_{}s'.format(entity_type)] = counts


def _integrate_institute_stats(stats, query_stats, entity_type):
    try:
        counts = query_stats.counts
    except AttributeError:
        counts = query_stats['counts']
    try:
        code = query_stats.instituteCode
    except AttributeError:
        code = query_stats['instituteCode']

    try:
        name = query_stats.name
    except AttributeError:
        name = query_stats['name']

    if counts:
        if code not in stats:
            stats[code] = {'instituteCode': code, 'name': name,
                           'num_accessions': 0, 'num_accessionsets': 0}

        stats[code]['num_{}s'.format(entity_type)] = counts


def _integrate_taxa_stats(stats, query_stats, entity_type):
    try:
        counts = query_stats['counts']
    except (AttributeError, TypeError):
        counts = query_stats.counts
    try:
        rank = query_stats['rank__name']
    except TypeError:
        rank = query_stats.rank.name
    try:
        taxon = query_stats['name']
    except TypeError:
        taxon = query_stats.taxon_name

    if counts:
        if rank not in stats:
            stats[rank] = {}
        if taxon not in stats[rank]:
            stats[rank][taxon] = {'num_accessions': 0,
                                  'num_accessionsets': 0}
        stats[rank][taxon]['num_{}s'.format(entity_type)] = counts


class Country(models.Model):
    country_id = models.AutoField(primary_key=True, editable=False)
    code = models.CharField(max_length=4, db_index=True, unique=True)
    name = models.CharField(max_length=255, db_index=True, unique=True)

    class Meta:
        db_table = 'vavilov_country'

    def __str__(self):
        return '{}({})'.format(self.name, self.code)

    @property
    def num_accessions(self):
        queryset = Accession.objects.filter(passports__country=self).distinct()
        return queryset.count()

    @property
    def num_accessionsets(self):
        queryset = AccessionSet.objects.filter(accessions__passports__country=self).distinct()
        return queryset.count()

    def stats_by_institute(self, user=None):
        stats = {}

        with connection.cursor() as cursor:
            cursor.execute(get_country_stats_raw_sql(country_id=self.country_id,
                                                     stats_type='institute',
                                                     entity_type='accession',
                                                     user=user))
            accession_stats = cursor.fetchall()

        with connection.cursor() as cursor:
            cursor.execute(get_country_stats_raw_sql(country_id=self.country_id,
                                                     stats_type='institute',
                                                     entity_type='accessionset',
                                                     user=user))
            accessionset_stats = cursor.fetchall()
#         accession_stats = Country.objects.raw(
#             get_country_stats_raw_sql(country_id=self.country_id,
#                                       stats_type='institute',
#                                       entity_type='accession',
#                                       user=user))

#         accessionset_stats = Country.objects.raw(
#             get_country_stats_raw_sql(country_id=self.country_id,
#                                       stats_type='institute',
#                                       entity_type='accessionset',
#                                       user=user))
#         print(accession_stats.columns)
        for row in accession_stats:
            row = {'instituteCode': row[1], 'name': row[2], 'counts': row[3]}
            _integrate_institute_stats(stats, row, 'accession')
        for row in accessionset_stats:
            row = {'instituteCode': row[1], 'name': row[2], 'counts': row[3]}
            _integrate_institute_stats(stats, row, 'accessionset')
        return sorted(stats.values(), key=itemgetter('num_accessions'),
                      reverse=True)

    def stats_by_taxa(self, user=None):
        stats = {}
        accession_stats = Taxon.objects.raw(
            get_country_stats_raw_sql(country_id=self.country_id,
                                      stats_type='taxa',
                                      entity_type='accession',
                                      user=user))
        accessionset_stats = Taxon.objects.raw(
            get_country_stats_raw_sql(country_id=self.country_id,
                                      stats_type='taxa',
                                      entity_type='accessionset',
                                      user=user))
        for row in accession_stats:
            _integrate_taxa_stats(stats, row, 'accession')
        for row in accessionset_stats:
            _integrate_taxa_stats(stats, row, 'accessionset')
        return stats


class DataSource(models.Model):
    data_source_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20, db_index=True, unique=True)
    kind = models.CharField(max_length=100)

    def __str__(self):
        return self.code

    class Meta:
        db_table = 'vavilov_data_source'

    @property
    def num_passports(self):
        return Passport.objects.filter(data_source=self).count()


class Accession(models.Model):
    accession_id = models.AutoField(primary_key=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField()
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    germplasm_number = models.CharField(max_length=100, db_index=True)
    is_available = models.NullBooleanField()
    conservation_status = models.CharField(max_length=50, null=True)
    is_save_duplicate = models.NullBooleanField()
    data = JSONField()

    class Meta:
        unique_together = ('institute', 'germplasm_number')
        db_table = 'vavilov_accession'

    @property
    def genera(self):
        genera = Taxon.objects.filter(passport__accession=self,
                                      rank__name='genus').distinct()
        return genera.values_list('name', flat=True)

    @property
    def countries(self):
        queryset = Country.objects.filter(passport__accession=self).distinct()
        return queryset.values_list('code', flat=True)


class AccessionSet(models.Model):
    accessionset_id = models.AutoField(primary_key=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField()
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE)
    accessionset_number = models.CharField(max_length=100, db_index=True,
                                           null=True, unique=True)
    accessions = models.ManyToManyField(Accession)
    data = JSONField()

    class Meta:
        db_table = 'vavilov_accessionset'

    @property
    def genera(self):
        genera = Taxon.objects.filter(passport__accession__accessionset=self,
                                      rank__name='genus').distinct()
        return genera.values_list('name', flat=True)

    @property
    def countries(self):
        queryset = Country.objects.filter(passport__accession__accessionset=self).distinct()
        return queryset.values_list('code', flat=True)

    @property
    def latitudes(self):
        queryset = Passport.objects.filter(accession__accessionset=self).distinct()
        return queryset.values_list('latitude', flat=True)

    @property
    def longitudes(self):
        queryset = Passport.objects.filter(accession__accessionset=self).distinct()
        return queryset.values_list('longitude', flat=True)


class Rank(models.Model):
    rank_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    level = models.IntegerField()

    class Meta:
        db_table = 'vavilov_rank'


class Taxon(models.Model):
    taxon_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    rank = models.ForeignKey(Rank, on_delete=models.CASCADE)

    class Meta:
        db_table = 'vavilov_taxon'
        unique_together = ('name', 'rank')

    @property
    def num_accessions(self):
        query = Accession.objects.filter(passports__taxa=self)
        return query.distinct().count()

    @property
    def num_accessionsets(self):
        query = AccessionSet.objects.filter(accessions__passports__taxa=self)
        return query.distinct().count()


class Passport(models.Model):
    passport_id = models.AutoField(primary_key=True, editable=False)
    data = JSONField()
    data_source = models.ForeignKey(DataSource, null=True,
                                    on_delete=models.SET_NULL)
    institute = models.ForeignKey(Institute, db_index=True,
                                  related_name='passport_institute',
                                  on_delete=models.CASCADE)
    germplasm_number = models.CharField(max_length=100, db_index=True)
    accession = models.ForeignKey(Accession, on_delete=models.CASCADE,
                                  related_name='passports')
    taxa = models.ManyToManyField(Taxon)

    collection_number = models.CharField(max_length=255, db_index=True,
                                         null=True)
    collecting_institute = models.ForeignKey(
        Institute, db_index=True, null=True, on_delete=models.SET_NULL,
        related_name='passport_collecting_institute')
    # local name
    accession_name = models.CharField(max_length=255, db_index=True, null=True)
    crop_name = models.CharField(max_length=255, db_index=True, null=True)
    country = models.ForeignKey(Country, null=True, db_index=True,
                                on_delete=models.SET_NULL)
    state = models.CharField(max_length=255, db_index=True, null=True)
    province = models.CharField(max_length=255, db_index=True, null=True)
    municipality = models.CharField(max_length=255, db_index=True, null=True)
    location_site = models.TextField(db_index=True, null=True)
    biological_status = models.CharField(max_length=3, db_index=True,
                                         null=True)
    collection_source = models.CharField(max_length=3, db_index=True,
                                         null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=4, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=4, null=True)
    pdci = models.DecimalField(max_digits=4, decimal_places=2, null=True)

    class Meta:
        db_table = 'vavilov_passport'
        unique_together = ('institute', 'germplasm_number', 'data_source')

#  Phenotyping #


class Project(models.Model):
    project_id = models.AutoField(primary_key=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField()
    name = models.CharField(max_length=255, db_index=True)
    active = models.BooleanField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        db_table = 'vavilov_project'


class Study(models.Model):
    study_id = models.AutoField(primary_key=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    is_public = models.BooleanField()
    is_active = models.BooleanField(null=True)
    name = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.CharField(max_length=255)
    project = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL)
    data = JSONField()

    class Meta:
        db_table = 'vavilov_study'


class ScaleDataType(models.Model):
    scale_data_type_id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=255, db_index=True, unique=True)

    class Meta:
        db_table = 'vavilov_observation_data_type'


class Scale(models.Model):
    scale_id = models.AutoField(primary_key=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.CharField(max_length=255)
    data_type = models.ForeignKey(ScaleDataType, on_delete=models.CASCADE)
    decimal_places = models.IntegerField(null=True)
    max = models.FloatField(null=True)
    min = models.FloatField(null=True)

    class Meta:
        db_table = 'vavilov_scale'

    @property
    def valid_values(self):
        return ScaleCategory.objects.filter(scale=self).order_by('rank').values('value',
                                                                                'description')


class ScaleCategory(models.Model):
    scale_categories_id = models.AutoField(primary_key=True, editable=False)
    scale = models.ForeignKey(Scale, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
    rank = models.IntegerField(null=True)
    description = models.CharField(max_length=255)

    class Meta:
        db_table = 'vavilov_scale_category'
        unique_together = (('scale', 'value'),
                           ('scale', 'rank'),
                           ('scale', 'description'))


class Trait(models.Model):
    trait_id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.TextField()
    ontology = models.CharField(max_length=100, null=True)
    ontology_id = models.CharField(max_length=100, null=True)

    class Meta:
        db_table = 'vavilov_trait'
        unique_together = ('ontology', 'ontology_id')


class ObservationVariable(models.Model):
    observation_variable_id = models.AutoField(primary_key=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.CharField(max_length=255)
    trait = models.ForeignKey(Trait, null=True, on_delete=models.CASCADE)
    method = models.CharField(max_length=255)
    scale = models.ForeignKey(Scale, null=True, on_delete=models.CASCADE)

    class Meta:
        db_table = 'vavilov_observation_variable'
        unique_together = ('trait', 'method', 'scale')


class ObservationUnit(models.Model):
    observation_unit_id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    accession = models.ForeignKey(Accession, on_delete=models.CASCADE)
    level = models.CharField(max_length=255, db_index=True)
    replicate = models.CharField(max_length=255, null=True)
    study = models.ForeignKey(Study, on_delete=models.CASCADE)

    class Meta:
        db_table = 'vavilov_observation_unit'


class Plant(models.Model):
    plant_id = models.AutoField(primary_key=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255, unique=True, db_index=True)
    x = models.CharField(max_length=255, null=True)
    y = models.CharField(max_length=255, null=True)
    block_number = models.CharField(max_length=255, db_index=True, null=True)
    entry_number = models.CharField(max_length=255, db_index=True, null=True)
    plant_number = models.CharField(max_length=255, db_index=True, null=True)
    plot_number = models.CharField(max_length=255, db_index=True, null=True)
    observation_units = models.ManyToManyField(ObservationUnit)

    class Meta:
        db_table = 'vavilov_plant'


class Observation(models.Model):
    observation_id = models.AutoField(primary_key=True, editable=False)
    observation_variable = models.ForeignKey(ObservationVariable,
                                             on_delete=models.CASCADE)
    observation_unit = models.ForeignKey(ObservationUnit,
                                         on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    observer = models.CharField(max_length=255, null=True)
    creation_time = models.DateTimeField(null=True)

    class Meta:
        db_table = 'vavilov_observation'
        unique_together = ('observation_variable', 'observation_unit', 'value',
                           'observer', 'creation_time')

    @property
    def beauty_value(self):
        if self.observation_variable.scale.data_type.name in (NOMINAL, ORDINAL):
            cat = ScaleCategory.objects.get(scale=self.observation_variable.scale,
                                            value=self.value)

            return '{} ({})'.format(self.value, cat.description)
        return self.value


def _get_upload_path(instance, filename, prefix=None):
    study = instance.observation_unit.study.name
    accession = '{}-{}'.format(instance.observation_unit.accession.institute.code,
                               instance.observation_unit.accession.germplasm_number)

    suffix = splitext(filename)[1]
    filename = '{}_'.format(prefix) if prefix else ''
    filename += '{}_{}_{}{}'.format(study, accession,
                                    instance.observation_image_uid, suffix)
    return join(MEDIA_ROOT, PHENO_IMAGE_DIR, accession, study, filename)


def get_image_upload_path(instance, filename):
    return _get_upload_path(instance, filename)


def get_small_image_upload_path(instance, filename):
    return _get_upload_path(instance, filename, 'small')


def get_medium_image_upload_path(instance, filename):
    return _get_upload_path(instance, filename, 'medium')


class ObservationImage(models.Model):
    observation_image_id = models.AutoField(primary_key=True, editable=False)
    observation_image_uid = models.TextField(unique=True)
    observation_unit = models.ForeignKey(ObservationUnit,
                                         on_delete=models.CASCADE)
    image = models.ImageField(upload_to=get_image_upload_path, max_length=1000)
    image_medium = models.ImageField(upload_to=get_medium_image_upload_path,
                                     null=True, blank=True, max_length=1000)
    image_small = models.ImageField(upload_to=get_small_image_upload_path,
                                    null=True, blank=True, max_length=1000)
    observer = models.CharField(max_length=255, null=True)
    creation_time = models.DateTimeField(null=True)

    class Meta:
        db_table = 'vavilov_observation_images'

    def _create_thumbnail(self, size=(128, 128), kind='small'):
        """
        Create a thumbnail from a saved image
        Adapted from this gist: https://gist.github.com/valberg/2429288
        """

        if not self.image:
            return

        im = Image.open(self.image)
        pil_format = im.format

        if pil_format == 'JPEG':
            pil_type = 'jpeg'
            extension = 'jpg'
            django_type = 'image/jpg'

        if pil_format == 'PNG':
            pil_type = 'png'
            extension = 'png'
            django_type = 'image/png'

        try:
            self.image.seek(0)
            image = Image.open(io.BytesIO(self.image.read()))
            image.thumbnail(size, Image.ANTIALIAS)
            temp_handle = io.BytesIO()
            image.save(temp_handle, pil_type)
            temp_handle.seek(0)

            suf = SimpleUploadedFile(split(self.image.name)[-1],
                                     temp_handle.read(), content_type=django_type)
            field = self.image_small if kind == 'small' else self.image_medium
            field.save(
                '{}_{}.{}'.format(splitext(suf.name)[0], kind, extension),
                suf,
                save=False)
        except IOError as error:
            print("Cannot create {} for {}: {}".format(kind, self.image.name,
                                                       error))

    def save(self, *args, **kwargs):
        self._create_thumbnail(kind='small')
        self._create_thumbnail((600, 400), kind='medium')

        super(ObservationImage, self).save(*args, **kwargs)

    @property
    def accession(self):
        return '{}-{}'.format(self.observation_unit.accession.institute.code,
                              self.observation_unit.accession.germplasm_number)

    @property
    def study(self):
        return self.observation_unit.study.name
