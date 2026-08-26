# paiements/views.py
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .models import Paiement
from .services import paiement_resume
from .emails import notifier_admin_nouveau_paiement


class TelechargerPreuvePaiementAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, reference_interne):
        paiement = get_object_or_404(Paiement, reference_interne=reference_interne, utilisateur=request.user)
        fichier = request.FILES.get("preuve_paiement")
        if not fichier:
            return Response({"detail": "Aucun fichier fourni."}, status=400)

        paiement.preuve_paiement = fichier
        try:
            paiement.full_clean()
        except ValidationError as e:
            return Response({"detail": " ".join(e.messages)}, status=400)

        paiement.save()
        notifier_admin_nouveau_paiement(paiement)
        return Response(paiement_resume(paiement), status=200)


class MonPaiementStatutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, reference_interne):
        paiement = get_object_or_404(Paiement, reference_interne=reference_interne, utilisateur=request.user)
        return Response(paiement_resume(paiement))