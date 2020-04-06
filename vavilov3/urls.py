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

from django.urls.conf import path, include
from django.views.generic.base import TemplateView

from rest_framework.routers import DefaultRouter
from rest_framework.schemas import get_schema_view
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

import vavilov3
from vavilov3.views.institute import InstituteViewSet
from vavilov3.views.accession import AccessionViewSet
from vavilov3.views.country import CountryViewSet
from vavilov3.views.data_source import DataSourceViewSet
from vavilov3.views.user import UserViewSet
from vavilov3.views.group import GroupViewSet
from vavilov3.views.auth import CRFTokenObtainPairView
from vavilov3.views.accessionset import AccessionSetViewSet
from vavilov3.views.taxon import TaxonViewSet
from vavilov3.views.study import StudyViewSet
from vavilov3.views.observation_variable import ObservationVariableViewSet
from vavilov3.views.observation_unit import ObservationUnitViewSet
from vavilov3.views.plant import PlantViewSet
from vavilov3.views.observation import ObservationViewSet
from vavilov3.views.task import TaskViewSet
from vavilov3.views.scale import ScaleViewSet
from vavilov3.views.trait import TraitViewSet
from vavilov3.views.observation_image import ObservationImageViewSet
from vavilov3.views.seed_request import SeedRequestViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'institutes', InstituteViewSet)
router.register(r'countries', CountryViewSet)
router.register(r'data_sources', DataSourceViewSet)
router.register(r'taxa', TaxonViewSet, basename='taxon')
router.register(r'accessions', AccessionViewSet)
router.register(r'accessionsets', AccessionSetViewSet)
router.register(r'studies', StudyViewSet)
router.register(r'observation_variables', ObservationVariableViewSet)
router.register(r'observation_units', ObservationUnitViewSet)
router.register(r'plants', PlantViewSet)
router.register(r'observations', ObservationViewSet)
router.register(r'scales', ScaleViewSet)
router.register(r'traits', TraitViewSet)
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'observation_images', ObservationImageViewSet)
router.register(r'seed_requests', SeedRequestViewSet)

schema_view = get_schema_view(
    title="Vavilov3 Restful api",
    description="Api to work with genebank data",
    version=vavilov3.version
)

urlpatterns = [
    path('auth/token/', CRFTokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('schema/', schema_view, name='openapi-schema'),
    path('doc/', TemplateView.as_view(template_name='swagger-ui.html',
                                      extra_context={'schema_url': 'openapi-schema'}),
         name='swagger-ui'),
    path('redoc/', TemplateView.as_view(template_name='redoc.html',
                                        extra_context={'schema_url': 'openapi-schema'}),
         name='redoc'),
    path('api-auth/', include('rest_framework.urls',
                              namespace='rest_framework')),

    path('', include(router.urls))
]
