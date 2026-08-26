# paiements/urls.py
from django.urls import path
from .views import TelechargerPreuvePaiementAPIView, MonPaiementStatutAPIView

urlpatterns = [
    path("paiements/<uuid:reference_interne>/preuve/", TelechargerPreuvePaiementAPIView.as_view(), name="paiement-preuve-api"),
    path("paiements/<uuid:reference_interne>/statut/", MonPaiementStatutAPIView.as_view(), name="paiement-statut-api"),
]