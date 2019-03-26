"""vavilov3_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.urls.conf import include

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.static import static
from django.conf import settings

schema_view = get_schema_view(
    openapi.Info(
        title="Vavilov3 Restful api",
        default_version='v1',
        description="Api to work with genebank data",
        terms_of_service="",
        contact=openapi.Contact(email="test@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('vavilov3.urls')),
    path('api-auth/', include('rest_framework.urls',
                              namespace='rest_framework')),
    path('api/doc/', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
] + static('media', document_root=settings.MEDIA_ROOT)
