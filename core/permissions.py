# core/permissions.py
from rest_framework import permissions
from .models import Utilisateur
from .services import verifier_acces_qcm


class EstSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role == Utilisateur.Role.SUPER_ADMIN
        )


class EstAdminOrg(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role == Utilisateur.Role.ADMIN_ORG
        )


class EstCreateurOuAdminOrg(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role in [
                Utilisateur.Role.CREATEUR,
                Utilisateur.Role.ADMIN_ORG,
                Utilisateur.Role.SUPER_ADMIN,
            ]
        )


class EstMembreDeLOrganisation(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == Utilisateur.Role.SUPER_ADMIN:
            return True
        return obj.organisation_id == request.user.organisation_id


class PeutCorrigerTexteLibre(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role in [
                Utilisateur.Role.CREATEUR,
                Utilisateur.Role.ADMIN_ORG,
                Utilisateur.Role.SUPER_ADMIN,
            ]
        )


class PeutAccederQCM(permissions.BasePermission):
    """Vérifie l'accès pour PASSER un QCM (détail + soumission de tentative).
    Ne s'applique PAS au catalogue (QCMListView), qui reste ouvert à tout connecté.
    Tente de récupérer l'objet QCM via view.get_object() pour vérifier aussi les packs."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        qcm = None
        get_object = getattr(view, "get_object", None)
        if get_object is not None:
            try:
                qcm = get_object()
            except Exception:
                qcm = None  # objet pas encore résolvable à ce stade, on vérifie sans le pack

        autorise, motif = verifier_acces_qcm(request.user, qcm=qcm)

        if motif == "quota_atteint":
            self.message = "Vous avez atteint votre quota de QCM gratuits pour aujourd'hui."
        elif motif == "abonnement_organisation_requis":
            self.message = "Un abonnement actif est requis pour votre organisation."

        return autorise