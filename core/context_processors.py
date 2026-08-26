# core/context_processors.py
def notifications(request):
    if not request.user.is_authenticated:
        return {}

    from tentatives.models import Tentative
    user = request.user
    contexte = {}

    if user.role in ["createur", "admin_org", "super_admin"]:
        queryset = Tentative.objects.filter(statut=Tentative.Statut.ATTENTE_CORRECTION)
        if user.role != "super_admin":
            queryset = queryset.filter(qcm__organisation=user.organisation)
        contexte["nb_corrections_a_faire"] = queryset.count()

    if user.role == "super_admin":
        from paiements.models import Paiement
        contexte["nb_paiements_a_valider"] = Paiement.objects.filter(statut=Paiement.Statut.EN_ATTENTE).count()

    return contexte