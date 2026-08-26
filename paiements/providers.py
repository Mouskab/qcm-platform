# paiements/providers.py
from django.conf import settings
from django.urls import reverse


class PaiementProviderBase:
    """Contrat que TOUT fournisseur de paiement doit respecter."""

    def initier_paiement(self, paiement, request) -> dict:
        raise NotImplementedError

    def traiter_notification(self, request) -> dict:
        raise NotImplementedError


class ValidationManuelleProvider(PaiementProviderBase):
    """En l'absence de compte marchand actif chez un vrai agrégateur, TOUT
    paiement 'en ligne' passe aussi par une validation manuelle d'un admin
    (identique au flux cash) — pas d'auto-confirmation immédiate."""

    def initier_paiement(self, paiement, request):
        url = request.build_absolute_uri(
            reverse("paiement-en-attente", kwargs={"reference_interne": paiement.reference_interne})
        )
        return {"url_redirection": url, "reference_transaction": f"MANUEL-{paiement.reference_interne}"}

    def traiter_notification(self, request):
        # Pas de webhook réel tant qu'aucun agrégateur n'est branché —
        # la confirmation vient uniquement de l'action admin dans Django Admin.
        raise NotImplementedError("Aucun webhook actif : la validation se fait manuellement dans l'admin.")


def obtenir_provider() -> PaiementProviderBase:
    nom = getattr(settings, "PAIEMENT_PROVIDER", "validation_manuelle")

    if nom == "validation_manuelle":
        return ValidationManuelleProvider()

    # Futur, une fois les clés obtenues :
    # if nom == "cinetpay":
    #     from .providers_cinetpay import CinetPayProvider
    #     return CinetPayProvider()

    raise ValueError(f"Fournisseur de paiement inconnu : {nom}")