# paiements/urls_web.py
from django.urls import path
from .views_web import (
    InitierPaiementAbonnementView, InitierPaiementPackView,
    PaiementEnAttenteView, PaiementRetourView, WebhookPaiementView,
    PaiementsAValiderListView, PaiementValiderView, PaiementRefuserView,
)

urlpatterns = [
    path("abonnement/<int:abonnement_id>/payer/", InitierPaiementAbonnementView.as_view(), name="payer-abonnement"),
    path("pack/<int:achat_pack_id>/payer/", InitierPaiementPackView.as_view(), name="payer-pack"),
    path("retour/<uuid:reference_interne>/", PaiementRetourView.as_view(), name="paiement-retour"),
    path("en-attente/<uuid:reference_interne>/", PaiementEnAttenteView.as_view(), name="paiement-en-attente"),
    path("webhook/", WebhookPaiementView.as_view(), name="paiement-webhook"),

    path("a-valider/", PaiementsAValiderListView.as_view(), name="paiements-a-valider"),
    path("a-valider/<int:paiement_id>/valider/", PaiementValiderView.as_view(), name="paiement-valider"),
    path("a-valider/<int:paiement_id>/refuser/", PaiementRefuserView.as_view(), name="paiement-refuser"),
]