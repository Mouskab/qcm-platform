# tentatives/urls_web.py
from django.urls import path
from .views_web import (
    QCMCatalogueWebView, PasserQCMView,
    MesResultatsListView, ResultatTentativeDetailView,
    ATCorrigerListView, CorrigerTentativeView,
    ClassementQCMView,   
    EvolutionQcmWebView,
)

urlpatterns = [
    path("", QCMCatalogueWebView.as_view(), name="qcm-catalogue-web"),
    path("<int:pk>/passer/", PasserQCMView.as_view(), name="qcm-passer-web"),
    path("<int:pk>/classement/", ClassementQCMView.as_view(), name="qcm-classement-web"),   # ← nouveau
    path("resultats/", MesResultatsListView.as_view(), name="mes-resultats-web"),
    path("resultats/<int:pk>/", ResultatTentativeDetailView.as_view(), name="resultat-tentative-web"),
    path("a-corriger/", ATCorrigerListView.as_view(), name="a-corriger-liste-web"),
    path("a-corriger/<int:pk>/", CorrigerTentativeView.as_view(), name="corriger-tentative-web"),
    path("<int:qcm_id>/evolution/", EvolutionQcmWebView.as_view(), name="evolution-qcm-web"),
]



urlpatterns += [
    path("<int:qcm_id>/evolution/", EvolutionQcmWebView.as_view(), name="evolution-qcm-web"),
]