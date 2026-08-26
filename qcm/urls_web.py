# qcm/urls_web.py
from django.urls import path
from .views import (
    QCMListWebView, QCMCreateWebView, QCMUpdateWebView, QCMDeleteWebView,
    QCMQuestionsWebView, QuestionCreateWebView,
    QCMImporterQuestionsView, TelechargerModeleImportView,
)

urlpatterns = [
    path("", QCMListWebView.as_view(), name="qcm-liste-web"),
    path("creer/", QCMCreateWebView.as_view(), name="qcm-creer-web"),
    path("<int:pk>/modifier/", QCMUpdateWebView.as_view(), name="qcm-modifier-web"),
    path("<int:pk>/supprimer/", QCMDeleteWebView.as_view(), name="qcm-supprimer-web"),
    path("<int:pk>/questions/", QCMQuestionsWebView.as_view(), name="qcm-questions-web"),
    path("<int:qcm_pk>/questions/ajouter/", QuestionCreateWebView.as_view(), name="question-creer-web"),
    path("<int:qcm_pk>/importer/", QCMImporterQuestionsView.as_view(), name="qcm-importer-web"),
    path("modele-import.xlsx", TelechargerModeleImportView.as_view(), name="modele-import-questions"),
]