# abonnements/views.py
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from paiements.models import Paiement
from paiements.services import paiement_resume
from .models import PlanAbonnement, Abonnement, Pack, AchatPack
from .serializers import PlanAbonnementSerializer, PackSerializer

DUREE_EN_JOURS = {"mensuel": 30, "trimestriel": 90, "annuel": 365}


class PlanAbonnementListView(generics.ListAPIView):
    serializer_class = PlanAbonnementSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = PlanAbonnement.objects.filter(actif=True)
        user = self.request.user
        if user and user.is_authenticated:
            type_cible = "organisation" if user.organisation_id else "individuel"
            queryset = queryset.filter(type_cible=type_cible)
        return queryset


class SouscrireAbonnementView(APIView):
    """Même logique anti-doublon que le web : réutilise une demande en
    attente existante, ou signale un abonnement déjà actif."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        mode = request.data.get("mode", "online")
        plan = get_object_or_404(PlanAbonnement, id=plan_id, actif=True)
        user = request.user

        organisation, utilisateur = None, None
        if plan.type_cible == PlanAbonnement.TypeCible.ORGANISATION:
            if not user.organisation_id:
                return Response({"detail": "Vous devez appartenir à une organisation pour ce plan."}, status=400)
            organisation = user.organisation
        else:
            utilisateur = user

        filtre = {"organisation": organisation} if organisation else {"utilisateur": utilisateur}
        existant = Abonnement.objects.filter(
            plan=plan, statut__in=[Abonnement.Statut.EN_ATTENTE_PAIEMENT, Abonnement.Statut.ACTIF], **filtre
        ).order_by("-date_creation").first()

        if existant:
            if existant.statut == Abonnement.Statut.ACTIF:
                return Response({"detail": "Vous avez déjà un abonnement actif pour ce plan.", "deja_actif": True})
            paiement_existant = existant.paiements.filter(statut=Paiement.Statut.EN_ATTENTE).first()
            if paiement_existant:
                return Response(paiement_resume(paiement_existant))

        maintenant = timezone.now()
        abonnement = Abonnement.objects.create(
            plan=plan, organisation=organisation, utilisateur=utilisateur,
            date_debut=maintenant, date_fin=maintenant + timedelta(days=DUREE_EN_JOURS[plan.duree]),
            statut=Abonnement.Statut.EN_ATTENTE_PAIEMENT,
        )
        paiement = Paiement.objects.create(
            abonnement=abonnement, utilisateur=user, montant=plan.prix, devise=plan.devise,
            mode=Paiement.Mode.CASH if mode == "cash" else Paiement.Mode.MOBILE_MONEY,
            fournisseur="cash" if mode == "cash" else "validation_manuelle",
        )
        return Response(paiement_resume(paiement), status=201)


class PackListAPIView(generics.ListAPIView):
    serializer_class = PackSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Pack.objects.filter(actif=True).select_related("thematique")


class AcheterPackAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pack_id):
        pack = get_object_or_404(Pack, id=pack_id, actif=True)
        mode = request.data.get("mode", "online")
        user = request.user

        achat = AchatPack.objects.filter(utilisateur=user, pack=pack).first()
        if achat:
            if achat.statut == AchatPack.Statut.ACTIF:
                return Response({"detail": "Vous possédez déjà ce pack.", "deja_actif": True})
            paiement_existant = achat.paiements.filter(statut=Paiement.Statut.EN_ATTENTE).first()
            if paiement_existant:
                return Response(paiement_resume(paiement_existant))
        else:
            achat = AchatPack.objects.create(utilisateur=user, pack=pack, statut=AchatPack.Statut.EN_ATTENTE_PAIEMENT)

        paiement = Paiement.objects.create(
            achat_pack=achat, utilisateur=user, montant=pack.prix, devise=pack.devise,
            mode=Paiement.Mode.CASH if mode == "cash" else Paiement.Mode.MOBILE_MONEY,
            fournisseur="cash" if mode == "cash" else "validation_manuelle",
        )
        return Response(paiement_resume(paiement), status=201)