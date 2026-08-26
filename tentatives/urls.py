# tentatives/urls.py
from django.urls import path
from .views import (
    SoumettreTentativeView, MesTentativesView, EvolutionQcmView,
    ClassementQcmAPIView, CorrigerReponseTexteLibreView,
)

urlpatterns = [
    path("tentatives/soumettre/", SoumettreTentativeView.as_view(), name="soumettre-tentative"),
    path("tentatives/mes-tentatives/", MesTentativesView.as_view(), name="mes-tentatives"),
    path("tentatives/evolution/<int:qcm_id>/", EvolutionQcmView.as_view(), name="evolution-qcm"),
    path("tentatives/classement/<int:qcm_id>/", ClassementQcmAPIView.as_view(), name="classement-qcm-api"),
    path("tentatives/corriger/<int:reponse_id>/", CorrigerReponseTexteLibreView.as_view(), name="corriger-reponse"),
]