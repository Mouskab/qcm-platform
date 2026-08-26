# abonnements/models.py
from django.db import models
from core.models import Organisation, Utilisateur
# abonnements/models.py (ajouter)
from qcm.models import Thematique,QCM


class PlanAbonnement(models.Model):
    """Défini par le Super Admin. Propagé au mobile via l'API (sync dynamique)."""

    class TypeCible(models.TextChoices):
        ORGANISATION = "organisation", "Organisation"
        INDIVIDUEL = "individuel", "Utilisateur individuel"

    class Duree(models.TextChoices):
        MENSUEL = "mensuel", "Mensuel"
        TRIMESTRIEL = "trimestriel", "Trimestriel"
        ANNUEL = "annuel", "Annuel"

    nom = models.CharField(max_length=100)
    type_cible = models.CharField(max_length=20, choices=TypeCible.choices)
    duree = models.CharField(max_length=20, choices=Duree.choices)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=10, default="XOF")  # Franc CFA

    # Limites (utilisées uniquement pour les plans "organisation")
    nb_qcm_max = models.PositiveIntegerField(null=True, blank=True, help_text="null = illimité")
    nb_utilisateurs_max = models.PositiveIntegerField(null=True, blank=True, help_text="null = illimité")

    actif = models.BooleanField(default=True)  # permet de désactiver un plan sans le supprimer
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.get_duree_display()}) - {self.prix} {self.devise}"


class Abonnement(models.Model):
    """Souscription active — soit pour une organisation, soit pour un individuel."""

    class Statut(models.TextChoices):
        ACTIF = "actif", "Actif"
        EXPIRE = "expire", "Expiré"
        ANNULE = "annule", "Annulé"
        EN_ATTENTE_PAIEMENT = "en_attente", "En attente de paiement"

    plan = models.ForeignKey(PlanAbonnement, on_delete=models.PROTECT, related_name="abonnements")

    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE,
        related_name="abonnements", null=True, blank=True
    )
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE,
        related_name="abonnements", null=True, blank=True
    )

    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE_PAIEMENT)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(organisation__isnull=False, utilisateur__isnull=True) |
                    models.Q(organisation__isnull=True, utilisateur__isnull=False)
                ),
                name="abonnement_org_ou_utilisateur_exclusif"
            )
        ]

    def __str__(self):
        cible = self.organisation or self.utilisateur
        return f"{cible} - {self.plan} ({self.statut})"




class Pack(models.Model):
    """Accès ciblé et permanent à une thématique précise, acheté une fois pour toutes
    (contrairement à un Abonnement classique, qui a une durée et couvre tout le catalogue)."""

    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thematique = models.ForeignKey(Thematique, on_delete=models.CASCADE, related_name="packs")
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=10, default="XOF")
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} — {self.prix} {self.devise}"


class AchatPack(models.Model):
    """Souscription à un pack — PAS de date_fin, l'accès est permanent une fois payé."""

    class Statut(models.TextChoices):
        EN_ATTENTE_PAIEMENT = "en_attente", "En attente de paiement"
        ACTIF = "actif", "Actif"

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="achats_packs")
    pack = models.ForeignKey(Pack, on_delete=models.PROTECT, related_name="achats")
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE_PAIEMENT)
    date_achat = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("utilisateur", "pack")  # empêche d'acheter 2 fois le même pack

    def __str__(self):
        return f"{self.utilisateur} — {self.pack} ({self.statut})"