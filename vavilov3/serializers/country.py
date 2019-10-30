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

from rest_framework import serializers

from vavilov3.models import Country
from rest_framework.exceptions import ValidationError
from vavilov3.views import format_error_message


class CountrySerializer(serializers.ModelSerializer):
    stats_by_institute = serializers.SerializerMethodField('_stats_by_institutes')
    stats_by_taxa = serializers.SerializerMethodField('_stats_by_taxa')

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        # Instantiate the superclass normally
        super(serializers.ModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            if not set(fields).issubset(self.fields):
                raise ValidationError(format_error_message('Passed fields are not allowed'))
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        else:
            self.fields.pop('stats_by_institute')
            self.fields.pop('stats_by_taxa')

    class Meta:
        model = Country
        fields = ('code', 'name', 'num_accessions', 'num_accessionsets',
                  'stats_by_institute', 'stats_by_taxa')

    def _stats_by_institutes(self, obj):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return obj.stats_by_institute(user)

    def _stats_by_taxa(self, obj):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        return obj.stats_by_taxa(user)
