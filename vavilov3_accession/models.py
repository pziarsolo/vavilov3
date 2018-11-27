from django.db import models
from django.contrib.auth.models import Group as DjangoGroup
from django.contrib.postgres.fields.jsonb import JSONField

from django.contrib.auth.models import AbstractUser
from django.db.models.aggregates import Count


class User(AbstractUser):
    pass


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

    @property
    def stats_by_country(self):
        return
        stats = {}
        accession_query = Country.objects.filter(
            passport__accession__institute=self)
        accession_stats = accession_query.annotate(
            _num_accessions=Count('passport__country'))
        for country in accession_stats:
            if country._num_accessions:
                stats[country.code] = {
                    'code': country.code, 'name': country.name,
                    'num_accessions': country._num_accessions,
                    'num_accessionsets': 0}

        accessionset_query = Country.objects.filter(
            passport__accession__accessionset__institute=self).distinct('passport__accession__accessionset')

        accessionset_stats = accessionset_query.annotate(
            _num_accessionsets=Count('passport__country'))

        for country in accessionset_stats:
            if country._num_accessionsets:

                if country.code in stats:
                    stats[country.code]['num_accessionsets'] = country._num_accessionsets
                else:
                    stats[country.code] = {
                        'code': country.code, 'name': country.name,
                        'num_accessions': 0,
                        'num_accessionsets': country._num_accessionsets}

                print(country._num_accessionsets)

        return stats.values()

    @property
    def stats_by_taxa(self):
        pass


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
