# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from core.views import (
    IndexView, OrganisationHomeView, ConnexionView, InscriptionWebView,
    MembresListView, AjoutMembreView, OrganisationBrandingView,
    ProfilWebView, ChangerMotDePasseWebView,
    MembreUpdateView, MembreDeleteView,
    GroupesListView, GroupeCreateView, GroupeUpdateView, GroupeDeleteView,
    DashboardOrganisationView, MentionsLegalesView, ConfidentialiteView, CguView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- API (Django REST Framework) ---
    path("api/", include("core.urls")),
    path("api/", include("qcm.urls")),
    path("api/", include("tentatives.urls")),
    path("api/", include("abonnements.urls")),

    # --- Pages publiques ---
    path("", IndexView.as_view(), name="index"),
    path("organisation/<int:pk>/", OrganisationHomeView.as_view(), name="organisation-home"),

    # --- Authentification web (sessions) ---
    path("compte/inscription/", InscriptionWebView.as_view(), name="inscription-web"),
    path("compte/connexion/", ConnexionView.as_view(), name="connexion"),
    path("compte/deconnexion/", auth_views.LogoutView.as_view(), name="deconnexion"),
    path("compte/profil/", ProfilWebView.as_view(), name="profil-web"),
    path("compte/changer-mot-de-passe/", ChangerMotDePasseWebView.as_view(), name="changer-mot-de-passe-web"),

    path("compte/mot-de-passe-oublie/",
         auth_views.PasswordResetView.as_view(template_name="registration/mot_de_passe_oublie.html"),
         name="password_reset"),
    path("compte/mot-de-passe-oublie/envoye/",
         auth_views.PasswordResetDoneView.as_view(template_name="registration/mot_de_passe_oublie_envoye.html"),
         name="password_reset_done"),
    path("compte/reinitialiser/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/reinitialiser_mot_de_passe.html"),
         name="password_reset_confirm"),
    path("compte/reinitialiser/termine/",
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/reinitialisation_terminee.html"),
         name="password_reset_complete"),

    # --- Gestion des QCM (dashboard créateur/admin) ---
    path("mes-qcm/", include("qcm.urls_web")),

    # --- Catalogue, passage de QCM, résultats, correction (web) ---
    path("qcm-disponibles/", include("tentatives.urls_web")),

    # --- Organisation : membres, groupes, branding, tableau de bord ---
    path("organisation/membres/", MembresListView.as_view(), name="membres-liste"),
    path("organisation/membres/ajouter/", AjoutMembreView.as_view(), name="membre-ajouter"),
    path("organisation/membres/<int:pk>/modifier/", MembreUpdateView.as_view(), name="membre-modifier"),
    path("organisation/membres/<int:pk>/supprimer/", MembreDeleteView.as_view(), name="membre-supprimer"),

    path("organisation/groupes/", GroupesListView.as_view(), name="groupes-liste"),
    path("organisation/groupes/creer/", GroupeCreateView.as_view(), name="groupe-creer"),
    path("organisation/groupes/<int:pk>/modifier/", GroupeUpdateView.as_view(), name="groupe-modifier"),
    path("organisation/groupes/<int:pk>/supprimer/", GroupeDeleteView.as_view(), name="groupe-supprimer"),

    path("organisation/personnaliser/", OrganisationBrandingView.as_view(), name="organisation-branding"),
    path("organisation/tableau-de-bord/", DashboardOrganisationView.as_view(), name="dashboard-organisation-web"),

    path("legal/mentions-legales/", MentionsLegalesView.as_view(), name="mentions-legales"),
    path("legal/confidentialite/", ConfidentialiteView.as_view(), name="confidentialite"),
    path("legal/cgu/", CguView.as_view(), name="cgu"),

    # --- Abonnements & packs (web) ---
    path("abonnement/", include("abonnements.urls_web")),

    # --- Paiements (web) ---
    path("paiements/", include("paiements.urls_web")),
    path("api/", include("paiements.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)