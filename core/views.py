# core/views.py
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UtilisateurSerializer, InscriptionSerializer
from django.views.generic import TemplateView, DetailView
from .models import Organisation
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .forms import InscriptionForm
from .models import Utilisateur, Organisation, ProfilCreateur
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .forms import AjoutMembreForm
from django.views.generic.edit import UpdateView
from .forms import OrganisationBrandingForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from .forms import ProfilForm
from django.views.generic.edit import DeleteView
from django.views.generic import TemplateView
from tentatives.services import calculer_stats_organisation
from django.views.generic import ListView
from .forms import GroupeForm
from .models import GroupeOrganisation
from django.core.cache import cache
from django.contrib.auth.views import LoginView
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions as drf_permissions
from .services import possede_abonnement_actif, quota_restant_aujourdhui
from .emails import envoyer_email_bienvenue

from .emails import envoyer_email_bienvenue

class InscriptionView(generics.CreateAPIView):
    queryset = Utilisateur.objects.all()
    serializer_class = InscriptionSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        utilisateur = serializer.save()
        envoyer_email_bienvenue(utilisateur)


class ProfilView(generics.RetrieveUpdateAPIView):
    """Endpoint protégé : l'utilisateur connecté voit/modifie SON propre profil"""
    serializer_class = UtilisateurSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Toujours retourner l'utilisateur connecté, jamais un autre par son ID
        return self.request.user




class IndexView(TemplateView):
    template_name = "index.html"


class OrganisationHomeView(DetailView):
    model = Organisation
    template_name = "organisations/home.html"
    context_object_name = "organisation"





class ConnexionView(LoginView):
    template_name = "registration/connexion.html"

    def post(self, request, *args, **kwargs):
        cle_cache = f"tentatives_connexion_{request.META.get('REMOTE_ADDR')}"
        tentatives = cache.get(cle_cache, 0)

        if tentatives >= 8:
            messages.error(request, "Trop de tentatives. Réessayez dans quelques minutes.")
            return self.render_to_response(self.get_context_data())

        response = super().post(request, *args, **kwargs)

        if not request.user.is_authenticated:
            cache.set(cle_cache, tentatives + 1, timeout=300)  # 5 minutes

        return response


# core/views.py

class InscriptionWebView(CreateView):
    form_class = InscriptionForm
    template_name = "registration/inscription.html"
    success_url = reverse_lazy("qcm-liste-web")

    def form_valid(self, form):
        response = super().form_valid(form)

        # Si la personne s'inscrit comme admin d'organisation,
        # on crée l'Organisation et on la rattache immédiatement
        if self.object.role == Utilisateur.Role.ADMIN_ORG:
            organisation = Organisation.objects.create(
                nom=form.cleaned_data["nom_organisation"],
                autorise_multi_admin=True,  # valeur par défaut, modifiable ensuite dans l'admin
            )
            self.object.organisation = organisation
            self.object.save()

        login(self.request, self.object)
        return response

    def form_valid(self, form):
        response = super().form_valid(form)

        if self.object.role == Utilisateur.Role.ADMIN_ORG:
            organisation = Organisation.objects.create(
                nom=form.cleaned_data["nom_organisation"],
                autorise_multi_admin=True,
            )
            self.object.organisation = organisation
            self.object.save()

        envoyer_email_bienvenue(self.object)
        login(self.request, self.object)
        return response




class EstAdminOrgMixin(UserPassesTestMixin):
    """Seul un admin d'organisation AVEC une organisation assignée peut gérer des membres.
    Le Super Admin n'a pas vocation à gérer les membres d'une organisation via cette vue."""
    def test_func(self):
        user = self.request.user
        return user.role == Utilisateur.Role.ADMIN_ORG and user.organisation_id is not None

class MembresListView(LoginRequiredMixin, EstAdminOrgMixin, ListView):
    template_name = "core/membres_liste.html"
    context_object_name = "membres"
    paginate_by = 20

    def get_queryset(self):
        return Utilisateur.objects.filter(
            organisation=self.request.user.organisation
        ).exclude(id=self.request.user.id)




class AjoutMembreView(LoginRequiredMixin, EstAdminOrgMixin, CreateView):
    form_class = AjoutMembreForm
    template_name = "core/membre_formulaire.html"
    success_url = reverse_lazy("membres-liste")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organisation"] = self.request.user.organisation
        return kwargs

    def form_valid(self, form):
        membre = form.save(commit=False)
        membre.organisation = self.request.user.organisation

        mot_de_passe_temporaire = get_random_string(length=10)
        membre.set_password(mot_de_passe_temporaire)
        membre.save()

        send_mail(
            subject=f"Votre compte {self.request.user.organisation.nom} sur Zamse",
            message=(
                f"Bonjour {membre.username},\n\n"
                f"Un compte vient d'être créé pour vous sur Zamse.\n"
                f"Identifiant : {membre.username}\n"
                f"Mot de passe temporaire : {mot_de_passe_temporaire}\n\n"
                f"Connectez-vous et pensez à le changer dès que possible."
            ),
            from_email=None,
            recipient_list=[membre.email] if membre.email else [],
        )

        self.mot_de_passe_genere = mot_de_passe_temporaire
        self.membre_cree = membre
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("membres-liste")




class OrganisationBrandingView(LoginRequiredMixin, EstAdminOrgMixin, UpdateView):
    """L'admin d'organisation modifie SA PROPRE organisation, jamais une autre.
    On ne passe aucun pk dans l'URL — l'objet est déduit de l'utilisateur connecté."""
    model = Organisation
    form_class = OrganisationBrandingForm
    template_name = "core/organisation_branding.html"
    success_url = reverse_lazy("organisation-branding")

    def get_object(self, queryset=None):
        return self.request.user.organisation






class ProfilWebView(LoginRequiredMixin, UpdateView):
    """L'utilisateur modifie SES PROPRES informations, jamais celles d'un autre —
    même principe que OrganisationBrandingView : pas de pk dans l'URL."""
    form_class = ProfilForm
    template_name = "core/profil.html"
    success_url = reverse_lazy("profil-web")

    def get_object(self, queryset=None):
        return self.request.user


class ChangerMotDePasseWebView(LoginRequiredMixin, PasswordChangeView):
    template_name = "core/changer_mot_de_passe.html"
    success_url = reverse_lazy("profil-web")






# core/views.py — ajoute cette vérification dans MembreUpdateView

class MembreUpdateView(LoginRequiredMixin, EstAdminOrgMixin, UpdateView):
    form_class = AjoutMembreForm
    template_name = "core/membre_formulaire.html"
    success_url = reverse_lazy("membres-liste")

    def get_queryset(self):
        # Exclut l'admin connecté de son propre périmètre de modification via
        # cette vue : il ne doit jamais pouvoir accidentellement changer son
        # propre rôle et se retrouver bloqué hors de l'organisation.
        return Utilisateur.objects.filter(
            organisation=self.request.user.organisation
        ).exclude(id=self.request.user.id)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organisation"] = self.request.user.organisation
        return kwargs

    
# core/views.py — vérifie/complète MembreDeleteView

class MembreDeleteView(LoginRequiredMixin, EstAdminOrgMixin, DeleteView):
    template_name = "core/membre_confirmer_suppression.html"
    success_url = reverse_lazy("membres-liste")

    def get_queryset(self):
        return Utilisateur.objects.filter(
            organisation=self.request.user.organisation
        ).exclude(id=self.request.user.id)


class DashboardOrganisationView(LoginRequiredMixin, EstAdminOrgMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = calculer_stats_organisation(self.request.user.organisation)
        context["organisation"] = self.request.user.organisation
        return context



class GroupesListView(LoginRequiredMixin, EstAdminOrgMixin, ListView):
    template_name = "core/groupes_liste.html"
    context_object_name = "groupes"

    def get_queryset(self):
        return GroupeOrganisation.objects.filter(
            organisation=self.request.user.organisation
        ).prefetch_related("membres")


class GroupeCreateView(LoginRequiredMixin, EstAdminOrgMixin, CreateView):
    form_class = GroupeForm
    template_name = "core/groupe_formulaire.html"
    success_url = reverse_lazy("groupes-liste")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organisation"] = self.request.user.organisation
        return kwargs

    def form_valid(self, form):
        form.instance.organisation = self.request.user.organisation
        return super().form_valid(form)


class GroupeUpdateView(LoginRequiredMixin, EstAdminOrgMixin, UpdateView):
    form_class = GroupeForm
    template_name = "core/groupe_formulaire.html"
    success_url = reverse_lazy("groupes-liste")

    def get_queryset(self):
        # Sécurité : impossible de modifier le groupe d'une autre organisation
        return GroupeOrganisation.objects.filter(organisation=self.request.user.organisation)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organisation"] = self.request.user.organisation
        return kwargs


class GroupeDeleteView(LoginRequiredMixin, EstAdminOrgMixin, DeleteView):
    template_name = "core/groupe_confirmer_suppression.html"
    success_url = reverse_lazy("groupes-liste")

    def get_queryset(self):
        return GroupeOrganisation.objects.filter(organisation=self.request.user.organisation)





class MonQuotaView(APIView):
    """Renvoie l'état d'accès de l'utilisateur connecté : a-t-il un abonnement
    actif, et sinon, combien de QCM gratuits lui reste-t-il aujourd'hui."""
    permission_classes = [drf_permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        abonnement_actif = possede_abonnement_actif(user)

        quota_restant = None
        if not abonnement_actif and not user.organisation_id:
            quota_restant = quota_restant_aujourdhui(user)

        return Response({
            "abonnement_actif": abonnement_actif,
            "quota_restant": quota_restant,  # null = non applicable (a un abonnement, ou membre d'org)
        })

# core/views.py (ajouter)
class MentionsLegalesView(TemplateView):
    template_name = "legal/mentions_legales.html"


class ConfidentialiteView(TemplateView):
    template_name = "legal/confidentialite.html"


class CguView(TemplateView):
    template_name = "legal/cgu.html"

# core/views.py (ajouter)
class MesNotificationsView(APIView):
    """Renvoie les compteurs d'actions en attente pour l'utilisateur connecté :
    corrections à faire (créateur/admin), résultats en attente de correction (candidat)."""
    permission_classes = [drf_permissions.IsAuthenticated]

    def get(self, request):
        from tentatives.models import Tentative
        user = request.user
        donnees = {"corrections_a_faire": 0, "resultats_en_attente": 0}

        if user.role in ["createur", "admin_org", "super_admin"]:
            queryset = Tentative.objects.filter(statut=Tentative.Statut.ATTENTE_CORRECTION)
            if user.role != "super_admin":
                queryset = queryset.filter(qcm__organisation=user.organisation)
            donnees["corrections_a_faire"] = queryset.count()

        donnees["resultats_en_attente"] = Tentative.objects.filter(
            utilisateur=user, statut=Tentative.Statut.ATTENTE_CORRECTION
        ).count()

        return Response(donnees)