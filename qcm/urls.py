# qcm/urls.py
from django.urls import path
from .views import (
    ThematiqueListCreateView, QCMListView,
    QCMDetailView, QCMCreateView, QCMUpdateDeleteView
)

urlpatterns = [
    path("thematiques/", ThematiqueListCreateView.as_view(), name="thematiques"),
    path("qcm/", QCMListView.as_view(), name="qcm-liste"),
    path("qcm/creer/", QCMCreateView.as_view(), name="qcm-creer"),
    path("qcm/<int:pk>/", QCMDetailView.as_view(), name="qcm-detail"),
    path("qcm/<int:pk>/gerer/", QCMUpdateDeleteView.as_view(), name="qcm-gerer"),
]