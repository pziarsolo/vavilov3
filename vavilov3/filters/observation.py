from django_filters import rest_framework as filters

from vavilov3.models import Observation, ObservationVariable
from vavilov3.filters.shared import TermFilterMixin
from django_filters.filters import DateTimeFromToRangeFilter
from rest_framework.exceptions import ValidationError
from django.db.models.lookups import Transform
from django.db.models.fields import Field
from vavilov3.views import format_error_message


@Field.register_lookup
class IntegerValue(Transform):
    # Register this before you filter things, for example in models.py
    lookup_name = 'int'  # Used as object.filter(LeftField__int__gte, "777")
    bilateral = True  # To cast both left and right

    def as_sql(self, compiler, _):
        sql, params = compiler.compile(self.lhs)
        sql = 'CAST(%s AS FLOAT)' % sql
        return sql, params


class ObservationFilter(TermFilterMixin, filters.FilterSet):
    term = filters.CharFilter(label='term', method='term_filter')
    group = filters.CharFilter(field_name='observation_unit__study__group__name',
                               lookup_expr='exact')
    is_public = filters.BooleanFilter(field_name='observation_unit__study__is_public')
    study = filters.CharFilter(field_name='observation_unit__study__name',
                               lookup_expr='iexact')
    study_contains = filters.CharFilter(field_name='observation_unit__study__name',
                                        lookup_expr='icontains')
    studies = filters.CharFilter(label='studies', method='studies_filter')

    observation_variable = filters.CharFilter(field_name='observation_variable__name',
                                              lookup_expr='iexact')
    observation_variables = filters.CharFilter(field_name='observation_variable__name',
                                               lookup_expr='in')
    observation_variable_contains = filters.CharFilter(field_name='observation_variable__name',
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
    value_range_min = filters.CharFilter(method='value_range_min_filter')
    value_range_max = filters.CharFilter(method='value_range_max_filter')

    class Meta:
        model = Observation
        fields = {'observer': ['exact', 'iexact', 'icontains']}

    def value_range_min_filter(self, queryset, _, value):
        self._check_observation_variable_in_filter()
        queryset = queryset.filter(value__int__gte=int(value))
        return queryset

    def value_range_max_filter(self, queryset, _, value):
        self._check_observation_variable_in_filter()
        queryset = queryset.filter(value__int__lte=int(value))
        return queryset

    def _check_observation_variable_in_filter(self):
        if 'observation_variable' not in self.data.keys():
            msg = 'Can not use value_range filter if not filtered by observation variable'
            raise ValidationError(format_error_message(msg))
        try:
            observation_variable = ObservationVariable.objects.get(name=self.data['observation_variable'])
        except ObservationVariable.DoesNotExist:
            msg = 'Used observation_variable to filter does not exist'
            raise ValidationError(format_error_message(msg))

        if observation_variable.scale.data_type.name not in ('Numerical',):
            msg = "Used observation_variable's data type is not numeric"
            raise ValidationError(format_error_message(msg))

    def studies_filter(self, queryset, _, value):
        return queryset.filter(observation_unit__study__name__in=value.split(','))
