from django.urls.conf import path, include

from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from vavilov3_accession.views.institute import InstituteViewSet
from vavilov3_accession.views.accession import AccessionViewSet
from vavilov3_accession.views.country import CountryViewSet
from vavilov3_accession.views.data_source import DataSourceViewSet
from vavilov3_accession.views.user import UserViewSet
from vavilov3_accession.views.group import GroupViewSet
from vavilov3_accession.views.auth import CRFTokenObtainPairView
from vavilov3_accession.views.accessionset import AccessionSetViewSet
from vavilov3_accession.views.taxon import TaxonViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'institutes', InstituteViewSet)
router.register(r'countries', CountryViewSet)
router.register(r'data_sources', DataSourceViewSet)
router.register(r'taxa', TaxonViewSet, base_name='taxon')
router.register(r'accessions', AccessionViewSet)
router.register(r'accessionsets', AccessionSetViewSet)

urlpatterns = [
    path('auth/token/', CRFTokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('', include(router.urls))

]
