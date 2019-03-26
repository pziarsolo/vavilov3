from django_filters import rest_framework as filters

from django_filters.filters import DateTimeFromToRangeFilter
from vavilov3.models import ObservationImage


class ObservationImageFilter(filters.FilterSet):
    group = filters.CharFilter(field_name='observation_unit__study__group__name',
                               lookup_expr='exact')
    is_public = filters.BooleanFilter(field_name='observation_unit__study__is_public')
    study = filters.CharFilter(field_name='observation_unit__study__name',
                               lookup_expr='iexact')
    study_contains = filters.CharFilter(field_name='observation_unit__study__name',
                                        lookup_expr='icontains')

    observation_unit = filters.CharFilter(field_name='observation_unit__name',
                                          lookup_expr='iexact')
    observation_unit_contains = filters.CharFilter(field_name='observation_unit__name',
                                                   lookup_expr='icontains')
    plant = filters.CharFilter(field_name='observation_unit__plants__name',
                               lookup_expr='iexact')
    plant_contain = filters.CharFilter(field_name='observation_unit__plants__name',
                                       lookup_expr='icontains')
    accession_number = filters.CharFilter(field_name='observation_unit__accession__germplasm_number',
                                          lookup_expr='iexact')
    accession_number_contains = filters.CharFilter(field_name='observation_unit__accession__germplasm_number',
                                                   lookup_expr='icontains')
    accession_institute = filters.CharFilter(field_name='observation_unit__accession__institute__code',
                                             lookup_expr='iexact')
    accession_institute_contains = filters.CharFilter(field_name='observation_unit__accession__institute__code',
                                                      lookup_expr='icontains')
    created = DateTimeFromToRangeFilter(field_name='creation_time')

    class Meta:
        model = ObservationImage
        fields = {'observer': ['exact', 'iexact', 'icontains'],
                  'observation_image_uid': ['iexact']}
