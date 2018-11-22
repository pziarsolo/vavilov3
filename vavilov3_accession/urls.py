from django.urls.conf import path, include

from rest_framework.routers import DefaultRouter

from vavilov3_accession.views.institute import InstituteViewSet
from vavilov3_accession.views.accession import AccessionViewSet
from vavilov3_accession.views.country import CountryViewSet

router = DefaultRouter()
router.register(r'institutes', InstituteViewSet)
router.register(r'countries', CountryViewSet)
router.register(r'accessions', AccessionViewSet)

urlpatterns = [
    path('', include(router.urls))
]
