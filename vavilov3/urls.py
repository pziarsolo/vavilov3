from django.urls.conf import path, include

from rest_framework.routers import DefaultRouter

from vavilov3.views.institute import InstituteViewSet

router = DefaultRouter()
router.register(r'institutes', InstituteViewSet)

urlpatterns = [
    path('', include(router.urls))
]
