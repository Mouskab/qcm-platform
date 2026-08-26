# paiements/models.py
import uuid
from django.db import models
from core.models import Utilisateur
from abonnements.models import Abonnement, AchatPack
from django.core.validators import FileExtensionValidator
from core.validators import valider_taille_image, valider_contenu_image


class Paiement(models.Model):
    class Mode(models.TextChoices):
        MOBILE_MONEY = "mobile_money", "Mobile Money"
        CASH = "cash", "Cash (validation manuelle)"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        VALIDE = "valide", "Validé"
        REFUSE = "refuse", "Refusé"
        REMBOURSE = "rembourse", "Remboursé"

    # Référence interne, générée par NOUS, envoyée au fournisseur, et qu'il nous
    # renverra dans le webhook — c'est ce qui nous permet de retrouver CE paiement
    # précis, peu importe l'agrégateur utilisé.
    reference_interne = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Un paiement finance SOIT un abonnement, SOIT un achat de pack — jamais les deux,
    # jamais aucun (même logique de contrainte que sur le modèle Abonnement).
    abonnement = models.ForeignKey(
        Abonnement, on_delete=models.CASCADE, related_name="paiements", null=True, blank=True
    )
    achat_pack = models.ForeignKey(
        AchatPack, on_delete=models.CASCADE, related_name="paiements", null=True, blank=True
    )

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="paiements")
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=10, default="XOF")
    mode = models.CharField(max_length=20, choices=Mode.choices)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)

    fournisseur = models.CharField(max_length=30, blank=True, help_text="ex: cinetpay, paydunya, simulateur")
    reference_transaction = models.CharField(max_length=255, blank=True, null=True)
    url_redirection = models.URLField(blank=True, null=True)
    reponse_fournisseur = models.JSONField(blank=True, null=True)

    valide_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name="paiements_valides"
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    preuve_paiement = models.ImageField(
        upload_to="paiements/preuves/",
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
            valider_taille_image,
            valider_contenu_image,
        ],
        help_text="Capture d'écran de la confirmation de paiement (Mobile Money ou reçu)."
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(abonnement__isnull=False, achat_pack__isnull=True) |
                    models.Q(abonnement__isnull=True, achat_pack__isnull=False)
                ),
                name="paiement_abonnement_ou_pack_exclusif"
            )
        ]

    def __str__(self):
        cible = self.abonnement or self.achat_pack
        return f"Paiement {self.montant} {self.devise} — {cible} ({self.statut})"