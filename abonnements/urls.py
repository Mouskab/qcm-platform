# abonnements/urls.py
from django.urls import path
from .views import PlanAbonnementListView, SouscrireAbonnementView, PackListAPIView, AcheterPackAPIView

urlpatterns = [
    path("plans/", PlanAbonnementListView.as_view(), name="plans-liste-api"),
    path("abonnements/souscrire/", SouscrireAbonnementView.as_view(), name="abonnement-souscrire-api"),
    path("packs/", PackListAPIView.as_view(), name="packs-liste-api"),
    path("packs/<int:pack_id>/acheter/", AcheterPackAPIView.as_view(), name="pack-acheter-api"),
]