# paiements/services.py
from django.utils import timezone
from django.shortcuts import get_object_or_404
from abonnements.models import Abonnement, AchatPack
from .models import Paiement
from .providers import obtenir_provider


def paiement_resume(paiement):
    """Représentation compacte d'un paiement, utilisée par toutes les
    réponses API (souscription, achat pack, upload de preuve)."""
    cible = paiement.abonnement.plan.nom if paiement.abonnement else paiement.achat_pack.pack.nom
    return {
        "reference_interne": str(paiement.reference_interne),
        "montant": str(paiement.montant),
        "devise": paiement.devise,
        "statut": paiement.statut,
        "cible": cible,
        "a_preuve": bool(paiement.preuve_paiement),
    }


def initier_paiement_abonnement(abonnement, request):
    provider = obtenir_provider()
    paiement = Paiement.objects.create(
        abonnement=abonnement, utilisateur=request.user,
        montant=abonnement.plan.prix, devise=abonnement.plan.devise,
        mode=Paiement.Mode.MOBILE_MONEY, fournisseur="validation_manuelle",
    )
    resultat = provider.initier_paiement(paiement, request)
    paiement.url_redirection = resultat["url_redirection"]
    paiement.reference_transaction = resultat["reference_transaction"]
    paiement.save()
    return paiement


def initier_paiement_pack(achat_pack, request):
    provider = obtenir_provider()
    paiement = Paiement.objects.create(
        achat_pack=achat_pack, utilisateur=request.user,
        montant=achat_pack.pack.prix, devise=achat_pack.pack.devise,
        mode=Paiement.Mode.MOBILE_MONEY, fournisseur="validation_manuelle",
    )
    resultat = provider.initier_paiement(paiement, request)
    paiement.url_redirection = resultat["url_redirection"]
    paiement.reference_transaction = resultat["reference_transaction"]
    paiement.save()
    return paiement


def confirmer_paiement(reference_interne, statut: str, donnees_brutes: dict, valide_par=None):
    from core.emails import envoyer_recu_paiement

    paiement = get_object_or_404(Paiement, reference_interne=reference_interne)
    if paiement.statut != Paiement.Statut.EN_ATTENTE:
        return paiement

    paiement.reponse_fournisseur = donnees_brutes
    paiement.date_validation = timezone.now()
    paiement.valide_par = valide_par

    if statut == "valide":
        paiement.statut = Paiement.Statut.VALIDE
        if paiement.abonnement:
            paiement.abonnement.statut = Abonnement.Statut.ACTIF
            paiement.abonnement.save()
        elif paiement.achat_pack:
            paiement.achat_pack.statut = AchatPack.Statut.ACTIF
            paiement.achat_pack.save()
        envoyer_recu_paiement(paiement)
    else:
        paiement.statut = Paiement.Statut.REFUSE

    paiement.save()
    return paiement