from rest_framework_simplejwt.views import TokenObtainPairView

from vavilov3_accession.serializers.auth import CRFTokenObtainPairSerializer


class CRFTokenObtainPairView(TokenObtainPairView):
    serializer_class = CRFTokenObtainPairSerializer
