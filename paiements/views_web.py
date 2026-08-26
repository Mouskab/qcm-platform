# paiements/views_web.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from abonnements.models import Abonnement, AchatPack
from .models import Paiement
from .services import initier_paiement_abonnement, initier_paiement_pack, confirmer_paiement
from .forms import PreuvePaiementForm
from .emails import notifier_admin_nouveau_paiement
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.contrib import messages



class InitierPaiementAbonnementView(LoginRequiredMixin, View):
    def get(self, request, abonnement_id):
        abonnement = get_object_or_404(Abonnement, id=abonnement_id)
        est_proprietaire = (
            abonnement.utilisateur_id == request.user.id
            or (request.user.organisation_id and abonnement.organisation_id == request.user.organisation_id)
        )
        if not est_proprietaire:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied()

        paiement = initier_paiement_abonnement(abonnement, request)
        return redirect(paiement.url_redirection)


class InitierPaiementPackView(LoginRequiredMixin, View):
    def get(self, request, achat_pack_id):
        achat = get_object_or_404(AchatPack, id=achat_pack_id, utilisateur=request.user)
        paiement = initier_paiement_pack(achat, request)
        return redirect(paiement.url_redirection)




class PaiementEnAttenteView(LoginRequiredMixin, View):
    """Affiche l'attente de validation, et permet au candidat de joindre
    une preuve de paiement (capture Mobile Money, reçu, etc.)."""

    def get(self, request, reference_interne):
        paiement = get_object_or_404(Paiement, reference_interne=reference_interne, utilisateur=request.user)
        form = PreuvePaiementForm(instance=paiement)
        return render(request, "paiements/en_attente_validation.html", {"paiement": paiement, "form": form})

    def post(self, request, reference_interne):
        paiement = get_object_or_404(Paiement, reference_interne=reference_interne, utilisateur=request.user)
        form = PreuvePaiementForm(request.POST, request.FILES, instance=paiement)

        if form.is_valid():
            form.save()
            notifier_admin_nouveau_paiement(paiement)
            return render(request, "paiements/en_attente_validation.html", {
                "paiement": paiement, "form": form, "preuve_envoyee": True
            })

        return render(request, "paiements/en_attente_validation.html", {"paiement": paiement, "form": form})
    
class PaiementRetourView(LoginRequiredMixin, View):
    def get(self, request, reference_interne):
        paiement = get_object_or_404(Paiement, reference_interne=reference_interne, utilisateur=request.user)
        return render(request, "paiements/retour.html", {"paiement": paiement})


@method_decorator(csrf_exempt, name="dispatch")
class WebhookPaiementView(View):
    """Réservé à un futur agrégateur réel. Reste en place mais n'est appelé
    par personne tant que PAIEMENT_PROVIDER = 'validation_manuelle'."""
    def post(self, request):
        from .providers import obtenir_provider
        provider = obtenir_provider()
        resultat = provider.traiter_notification(request)
        confirmer_paiement(resultat["reference_interne"], resultat["statut"], resultat["donnees_brutes"])
        return HttpResponse("OK")





class EstSuperAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == "super_admin"


class PaiementsAValiderListView(LoginRequiredMixin, EstSuperAdminMixin, ListView):
    template_name = "paiements/a_valider_liste.html"
    context_object_name = "paiements"

    def get_queryset(self):
        return Paiement.objects.filter(
            statut=Paiement.Statut.EN_ATTENTE
        ).select_related("utilisateur", "abonnement__plan", "achat_pack__pack").order_by("date_creation")


class PaiementValiderView(LoginRequiredMixin, EstSuperAdminMixin, View):
    def post(self, request, paiement_id):
        paiement = get_object_or_404(Paiement, id=paiement_id, statut=Paiement.Statut.EN_ATTENTE)
        confirmer_paiement(paiement.reference_interne, "valide", {"validation": "manuelle_page_admin"}, valide_par=request.user)
        messages.success(request, f"Paiement de {paiement.utilisateur.username} validé et accès activé.")
        return redirect("paiements-a-valider")


class PaiementRefuserView(LoginRequiredMixin, EstSuperAdminMixin, View):
    def post(self, request, paiement_id):
        paiement = get_object_or_404(Paiement, id=paiement_id, statut=Paiement.Statut.EN_ATTENTE)
        confirmer_paiement(paiement.reference_interne, "refuse", {"validation": "manuelle_page_admin"}, valide_par=request.user)
        messages.warning(request, f"Paiement de {paiement.utilisateur.username} refusé.")
        return redirect("paiements-a-valider")