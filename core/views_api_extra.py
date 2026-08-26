# core/views_api_extra.py
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response


class ChangerMotDePasseAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ancien = request.data.get("ancien_mot_de_passe")
        nouveau = request.data.get("nouveau_mot_de_passe")
        user = request.user

        if not user.check_password(ancien):
            return Response({"detail": "Ancien mot de passe incorrect."}, status=400)
        try:
            validate_password(nouveau, user=user)
        except DjangoValidationError as e:
            return Response({"detail": " ".join(e.messages)}, status=400)

        user.set_password(nouveau)
        user.save()
        return Response({"detail": "Mot de passe mis à jour."})