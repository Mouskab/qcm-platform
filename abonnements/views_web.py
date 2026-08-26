# abonnements/views_web.py
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView
from django.shortcuts import render, redirect, get_object_or_404
from paiements.models import Paiement
import uuid
from .models import PlanAbonnement, Abonnement, Pack, AchatPack
from django.contrib import messages
from paiements.models import Paiement

DUREE_EN_JOURS = {"mensuel": 30, "trimestriel": 90, "annuel": 365}


class PlansWebView(LoginRequiredMixin, ListView):
    """Affiche les plans adaptés au type d'utilisateur connecté
    (individuel → plans individuels, membre d'org → plans organisation)"""
    template_name = "abonnements/plans.html"
    context_object_name = "plans"

    def get_queryset(self):
        type_cible = "organisation" if self.request.user.organisation_id else "individuel"
        return PlanAbonnement.objects.filter(actif=True, type_cible=type_cible)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        maintenant = timezone.now()

        if user.organisation_id:
            abonnement_actif = Abonnement.objects.filter(
                organisation=user.organisation, statut=Abonnement.Statut.ACTIF, date_fin__gte=maintenant
            ).first()
        else:
            abonnement_actif = Abonnement.objects.filter(
                utilisateur=user, statut=Abonnement.Statut.ACTIF, date_fin__gte=maintenant
            ).first()

        context["abonnement_actif"] = abonnement_actif
        return context


class SouscrireWebView(LoginRequiredMixin, View):
    def post(self, request, plan_id):
        plan = get_object_or_404(PlanAbonnement, id=plan_id, actif=True)
        user = request.user

        organisation, utilisateur = None, None
        if plan.type_cible == PlanAbonnement.TypeCible.ORGANISATION:
            if not user.organisation_id:
                return redirect("plans-web")
            organisation = user.organisation
        else:
            utilisateur = user

        # Empêche les doublons : si une demande est déjà en attente OU déjà
        # active pour ce même plan, on redirige vers elle plutôt que d'en créer une autre.
        filtre_existant = {"organisation": organisation} if organisation else {"utilisateur": utilisateur}
        abonnement_existant = Abonnement.objects.filter(
            plan=plan,
            statut__in=[Abonnement.Statut.EN_ATTENTE_PAIEMENT, Abonnement.Statut.ACTIF],
            **filtre_existant,
        ).order_by("-date_creation").first()

        if abonnement_existant:
            if abonnement_existant.statut == Abonnement.Statut.ACTIF:
                messages.info(request, "Vous avez déjà un abonnement actif pour ce plan.")
                return redirect("plans-web")
            # Une demande de paiement existe déjà : on redirige vers son paiement en cours
            paiement_existant = abonnement_existant.paiements.filter(statut=Paiement.Statut.EN_ATTENTE).first()
            if paiement_existant:
                return redirect("paiement-en-attente", reference_interne=paiement_existant.reference_interne)

        maintenant = timezone.now()
        abonnement = Abonnement.objects.create(
            plan=plan, organisation=organisation, utilisateur=utilisateur,
            date_debut=maintenant,
            date_fin=maintenant + timedelta(days=DUREE_EN_JOURS[plan.duree]),
            statut=Abonnement.Statut.EN_ATTENTE_PAIEMENT,
        )

        return redirect("payer-abonnement", abonnement_id=abonnement.id)


class PacksWebView(LoginRequiredMixin, ListView):
    template_name = "abonnements/packs.html"
    context_object_name = "packs"
    queryset = Pack.objects.filter(actif=True).select_related("thematique")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        packs_possedes = AchatPack.objects.filter(
            utilisateur=self.request.user, statut=AchatPack.Statut.ACTIF
        ).values_list("pack_id", flat=True)
        context["packs_possedes"] = set(packs_possedes)
        return context


class AcheterPackView(LoginRequiredMixin, View):
    """Crée l'achat de pack en 'en_attente_paiement', puis redirige vers le
    flux de paiement (même principe que SouscrireWebView)."""

    def post(self, request, pack_id):
        pack = get_object_or_404(Pack, id=pack_id, actif=True)

        # Empêche le doublon proprement (en plus de la contrainte base de données)
        achat_existant = AchatPack.objects.filter(utilisateur=request.user, pack=pack).first()
        if achat_existant:
            if achat_existant.statut == AchatPack.Statut.ACTIF:
                return redirect("packs-web")
            # Déjà tenté mais pas encore payé : on relance le paiement sur le même achat
            return redirect("payer-pack", achat_pack_id=achat_existant.id)

        achat = AchatPack.objects.create(
            utilisateur=request.user, pack=pack, statut=AchatPack.Statut.EN_ATTENTE_PAIEMENT
        )
        return redirect("payer-pack", achat_pack_id=achat.id)




class SouscrireCashWebView(LoginRequiredMixin, View):
    def post(self, request, plan_id):
        plan = get_object_or_404(PlanAbonnement, id=plan_id, actif=True)
        user = request.user

        organisation, utilisateur = None, None
        if plan.type_cible == PlanAbonnement.TypeCible.ORGANISATION:
            if not user.organisation_id:
                return redirect("plans-web")
            organisation = user.organisation
        else:
            utilisateur = user

        filtre_existant = {"organisation": organisation} if organisation else {"utilisateur": utilisateur}
        abonnement_existant = Abonnement.objects.filter(
            plan=plan,
            statut__in=[Abonnement.Statut.EN_ATTENTE_PAIEMENT, Abonnement.Statut.ACTIF],
            **filtre_existant,
        ).order_by("-date_creation").first()

        if abonnement_existant:
            if abonnement_existant.statut == Abonnement.Statut.ACTIF:
                messages.info(request, "Vous avez déjà un abonnement actif pour ce plan.")
                return redirect("plans-web")
            paiement_existant = abonnement_existant.paiements.filter(statut=Paiement.Statut.EN_ATTENTE).first()
            if paiement_existant:
                return redirect("paiement-en-attente", reference_interne=paiement_existant.reference_interne)

        maintenant = timezone.now()
        abonnement = Abonnement.objects.create(
            plan=plan, organisation=organisation, utilisateur=utilisateur,
            date_debut=maintenant,
            date_fin=maintenant + timedelta(days=DUREE_EN_JOURS[plan.duree]),
            statut=Abonnement.Statut.EN_ATTENTE_PAIEMENT,
        )

        paiement = Paiement.objects.create(
            abonnement=abonnement, utilisateur=user,
            montant=plan.prix, devise=plan.devise,
            mode=Paiement.Mode.CASH, fournisseur="cash",
        )

        return redirect("paiement-en-attente", reference_interne=paiement.reference_interne)


class AcheterPackCashWebView(LoginRequiredMixin, View):
    def post(self, request, pack_id):
        pack = get_object_or_404(Pack, id=pack_id, actif=True)
        user = request.user

        achat_existant = AchatPack.objects.filter(utilisateur=user, pack=pack).first()
        if achat_existant and achat_existant.statut == AchatPack.Statut.ACTIF:
            return redirect("packs-web")

        if not achat_existant:
            achat_existant = AchatPack.objects.create(
                utilisateur=user, pack=pack, statut=AchatPack.Statut.EN_ATTENTE_PAIEMENT
            )

        paiement = Paiement.objects.create(
            achat_pack=achat_existant, utilisateur=user,
            montant=pack.prix, devise=pack.devise,
            mode=Paiement.Mode.CASH,
            fournisseur="cash",
        )

        return render(request, "paiements/instructions_cash.html", {"paiement": paiement})