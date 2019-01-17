from operator import itemgetter

from numpy import histogram

from django.db import models, connection
from django.contrib.auth.models import Group as DjangoGroup
from django.contrib.postgres.fields.jsonb import JSONField

from vavilov3.raw_stat_sql_commands import (
    get_institute_stats_raw_sql, get_country_stats_raw_sql)


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
    is_active = models.BooleanField()
    name = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.CharField(max_length=255)
    project = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL)
    data = JSONField()

    class Meta:
        db_table = 'vavilov_study'


class ObservationDataType(models.Model):
    observation_data_type_id = models.AutoField(primary_key=True,
                                                editable=False)
    name = models.CharField(max_length=255, db_index=True, unique=True)

    class Meta:
        db_table = 'vavilov_observation_data_type'


class ObservationVariable(models.Model):
    observation_variable_id = models.AutoField(primary_key=True, editable=False)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255, db_index=True, unique=True)
    trait = models.CharField(max_length=255, db_index=True)
    description = models.CharField(max_length=255)
    method = models.CharField(max_length=255)
    data_type = models.ForeignKey(ObservationDataType, on_delete=models.CASCADE)
    unit = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'vavilov_observation_variable'
        unique_together = ('name', 'method', 'data_type', 'unit')


class ObservationUnit(models.Model):
    observation_unit_id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    accession = models.ForeignKey(Accession, on_delete=models.CASCADE)
    level = models.CharField(max_length=255)
    replicate = models.CharField(max_length=255)
    study = models.ForeignKey(Study, on_delete=models.CASCADE)


class Plant():
    x = models.CharField(max_length=255)
    y = models.CharField(max_length=255)
    block_number = models.CharField(max_length=255)
    entry_number = models.CharField(max_length=255)
    plant_number = models.CharField(max_length=255)
    plot_number = models.CharField(max_length=255)
    observation_units = models.ManyToManyField(ObservationUnit)


class Observation(models.Model):
    observation_id = models.AutoField(primary_key=True, editable=False)
    observation_variable = models.ForeignKey(ObservationVariable,
                                             on_delete=models.CASCADE)
    observation_unit = models.ForeignKey(ObservationUnit, on_delete=models.CASCADE)
    observationTimeStamp = models.DateField()
    observer = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
