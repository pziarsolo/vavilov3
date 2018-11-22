from django.urls.conf import path, include

from rest_framework.routers import DefaultRouter

from vavilov3_accession.views.institute import InstituteViewSet
from vavilov3_accession.views.accession import AccessionViewSet

router = DefaultRouter()
router.register(r'institutes', InstituteViewSet)
router.register(r'accessions', AccessionViewSet)

urlpatterns = [
    path('', include(router.urls))
]
