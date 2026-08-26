# tentatives/views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import Http404

from qcm.models import QCM
from core.permissions import PeutCorrigerTexteLibre, PeutAccederQCM
from core.services import qcm_visible_pour
from core.emails import envoyer_notification_correction
from .models import Tentative, ReponseUtilisateur
from .serializers import SoumissionTentativeSerializer, TentativeResultatSerializer
from .services import soumettre_tentative, LimiteTentativesAtteinte, evolution_tentatives_qcm, calculer_classement_qcm


class SoumettreTentativeView(APIView):
    permission_classes = [permissions.IsAuthenticated, PeutAccederQCM]

    def post(self, request):
        serializer = SoumissionTentativeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        qcm = get_object_or_404(QCM, id=data["qcm_id"], actif=True)
        try:
            tentative = soumettre_tentative(qcm, request.user, data["reponses"])
        except LimiteTentativesAtteinte:
            return Response({"detail": "Nombre de tentatives autorisées atteint pour ce QCM."}, status=status.HTTP_403_FORBIDDEN)
        return Response(TentativeResultatSerializer(tentative).data, status=status.HTTP_201_CREATED)


class MesTentativesView(generics.ListAPIView):
    serializer_class = TentativeResultatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Tentative.objects.filter(utilisateur=self.request.user).select_related("qcm").order_by("-date_debut")


class EvolutionQcmView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, qcm_id):
        qcm = get_object_or_404(QCM, id=qcm_id)
        return Response(evolution_tentatives_qcm(request.user, qcm))


class ClassementQcmAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, qcm_id):
        qcm = get_object_or_404(QCM, id=qcm_id, actif=True)
        if not qcm_visible_pour(request.user, qcm):
            raise Http404
        data = calculer_classement_qcm(qcm, utilisateur_courant=request.user)
        classement = [
            {"rang": e["rang"], "username": e["utilisateur"].username, "pourcentage": e["pourcentage"],
             "score_obtenu": e["score_obtenu"], "score_max": e["score_max"]}
            for e in data["classement"]
        ]
        return Response({
            "classement": classement,
            "nb_participants": data["nb_participants"],
            "rang_utilisateur_courant": data["rang_utilisateur_courant"],
        })


class CorrigerReponseTexteLibreView(APIView):
    permission_classes = [permissions.IsAuthenticated, PeutCorrigerTexteLibre]

    def post(self, request, reponse_id):
        reponse = get_object_or_404(ReponseUtilisateur, id=reponse_id)
        points = request.data.get("points_attribues")
        if points is None:
            return Response({"detail": "Le champ 'points_attribues' est requis."}, status=400)

        reponse.points_attribues = points
        reponse.corrige_par = request.user
        reponse.date_correction = timezone.now()
        reponse.save()

        tentative = reponse.tentative
        non_corrigees = tentative.reponses_utilisateur.filter(question__type_question="texte_libre", points_attribues__isnull=True).exists()
        if not non_corrigees:
            score_total = sum(r.points_attribues or 0 for r in tentative.reponses_utilisateur.all())
            tentative.score_obtenu = score_total
            tentative.statut = Tentative.Statut.CORRIGEE_COMPLETE
            tentative.save()
            envoyer_notification_correction(tentative)

        return Response({"detail": "Correction enregistrée.", "points_attribues": points})