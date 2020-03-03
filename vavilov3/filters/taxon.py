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

from django_filters import rest_framework as filters

from vavilov3.models import Taxon


class TaxonFilter(filters.FilterSet):
    accession_in_study = filters.CharFilter(label='Only_accession_in_study',
                                            method='only_in_studies')

    class Meta:
        model = Taxon
        fields = {'name': ['icontains']}

    def only_in_studies(self, queryset, _, value):
        return queryset.filter(passport__accession__observationunit__study__isnull=False).distinct().order_by('name')
