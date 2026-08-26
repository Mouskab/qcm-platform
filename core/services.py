# core/services.py
from django.utils import timezone
from .models import Utilisateur, ParametrePlateforme
from django.db.models import Q


def possede_abonnement_actif(user):
    """Abonnement classique (durée) actif — organisation OU individuel."""
    from abonnements.models import Abonnement

    if user.role == Utilisateur.Role.SUPER_ADMIN:
        return True

    maintenant = timezone.now()
    if user.organisation_id:
        return Abonnement.objects.filter(
            organisation=user.organisation, statut=Abonnement.Statut.ACTIF, date_fin__gte=maintenant
        ).exists()

    return Abonnement.objects.filter(
        utilisateur=user, statut=Abonnement.Statut.ACTIF, date_fin__gte=maintenant
    ).exists()


def possede_pack_actif_pour(user, qcm):
    """Vérifie si l'utilisateur a acheté un pack couvrant la thématique de ce QCM précis."""
    from abonnements.models import AchatPack
    return AchatPack.objects.filter(
        utilisateur=user,
        statut=AchatPack.Statut.ACTIF,
        pack__thematique=qcm.thematique,
    ).exists()


def nb_tentatives_aujourdhui(user):
    """Compte les QCM déjà passés aujourd'hui par cet utilisateur, tous QCM confondus."""
    from tentatives.models import Tentative
    aujourdhui = timezone.localdate()
    return Tentative.objects.filter(utilisateur=user, date_debut__date=aujourdhui).count()


def quota_restant_aujourdhui(user):
    """Retourne le nombre de tentatives gratuites encore disponibles aujourd'hui."""
    quota_max = ParametrePlateforme.instance().quota_qcm_gratuit_par_jour
    deja_utilisees = nb_tentatives_aujourdhui(user)
    return max(0, quota_max - deja_utilisees)


def verifier_acces_qcm(user, qcm=None):
    """
    Point d'entrée unique pour savoir si un utilisateur peut PASSER un QCM.
    qcm est optionnel : sans lui, on ne peut pas vérifier les packs.
    Ordre : Super Admin > abonnement actif > pack sur cette thématique > quota gratuit.
    Retourne (autorise: bool, motif: str|None).
    """
    if user.role == Utilisateur.Role.SUPER_ADMIN:
        return True, None

    if possede_abonnement_actif(user):
        return True, None

    if qcm is not None and possede_pack_actif_pour(user, qcm):
        return True, None

    if user.organisation_id:
        return False, "abonnement_organisation_requis"

    if quota_restant_aujourdhui(user) > 0:
        return True, None

    return False, "quota_atteint"




def qcm_visible_pour(user, qcm):
    """Vérifie si CE QCM précis doit apparaître/être accessible pour cet utilisateur,
    en tenant compte de la restriction par groupe."""
    if user.role == Utilisateur.Role.SUPER_ADMIN:
        return True
    if qcm.est_public:
        return True
    if qcm.organisation_id != user.organisation_id:
        return False
    if not qcm.groupes.exists():
        return True  # pas de restriction de groupe = visible à toute l'organisation
    return qcm.groupes.filter(membres=user).exists()


def qcm_queryset_visible_pour(user):
    """Version 'liste' de qcm_visible_pour, pour filtrer un catalogue entier
    en une seule requête plutôt que de boucler objet par objet.
    Utilisée à la fois par l'API et le web (DRY : une seule logique à maintenir)."""
    from qcm.models import QCM

    queryset = QCM.objects.filter(
        Q(est_public=True) | Q(organisation=user.organisation),
        actif=True,
    )

    if user.role == Utilisateur.Role.SUPER_ADMIN:
        return queryset

    # Exclut les QCM restreints à un groupe dont l'utilisateur ne fait pas partie
    queryset = queryset.filter(
        Q(groupes__isnull=True) | Q(groupes__membres=user)
    ).distinct()

    return queryset