# core/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import InscriptionView, ProfilView, MonQuotaView, MesNotificationsView
from .views_api_extra import ChangerMotDePasseAPIView
from .throttles import ConnexionRateThrottle


class TokenObtainPairThrottleView(TokenObtainPairView):
    throttle_classes = [ConnexionRateThrottle]


urlpatterns = [
    path("inscription/", InscriptionView.as_view(), name="inscription"),
    path("profil/", ProfilView.as_view(), name="profil"),
    path("profil/changer-mot-de-passe/", ChangerMotDePasseAPIView.as_view(), name="changer-mdp-api"),
    path("mon-quota/", MonQuotaView.as_view(), name="mon-quota"),
    path("mes-notifications/", MesNotificationsView.as_view(), name="mes-notifications"),
    path("token/", TokenObtainPairThrottleView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]