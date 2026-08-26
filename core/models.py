# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from .validators import valider_taille_image, valider_contenu_image


class Organisation(models.Model):
    nom = models.CharField(max_length=255)
    nom_affiche = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(
        upload_to="organisations/logos/",
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
            valider_taille_image,
            valider_contenu_image,
        ],
        help_text="Formats acceptés : JPG, PNG, WEBP — 2 Mo maximum."
    )
    couleur_primaire = models.CharField(max_length=7, default="#16233F")
    couleur_secondaire = models.CharField(max_length=7, default="#D9A441")
    autorise_multi_admin = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.nom


class Utilisateur(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        ADMIN_ORG = "admin_org", "Admin Organisation"
        CREATEUR = "createur", "Créateur de contenu"
        APPRENANT = "apprenant", "Apprenant"
        INDIVIDUEL = "individuel", "Utilisateur individuel"

    email = models.EmailField(unique=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE,
        related_name="membres", null=True, blank=True
    )
    telephone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class ProfilCreateur(models.Model):
    class StatutRemuneration(models.TextChoices):
        INTERNE = "interne", "Interne (non rémunéré)"
        FREELANCE = "freelance", "Freelance (rémunéré)"

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE,
        related_name="profil_createur"
    )
    statut_remuneration = models.CharField(
        max_length=20, choices=StatutRemuneration.choices,
        default=StatutRemuneration.INTERNE
    )
    taux_par_question = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Montant payé par question créée (si statut freelance)"
    )
    date_activation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"Profil créateur — {self.utilisateur.username} ({self.get_statut_remuneration_display()})"


class GroupeOrganisation(models.Model):
    """Un groupe (classe, promotion, cohorte...) au sein d'une organisation.
    Un membre peut appartenir à plusieurs groupes simultanément."""

    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="groupes")
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    membres = models.ManyToManyField(Utilisateur, related_name="groupes", blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} — {self.organisation.nom}"


class ParametrePlateforme(models.Model):
    """Singleton : une seule ligne existe toujours en base (pk=1)."""

    quota_qcm_gratuit_par_jour = models.PositiveIntegerField(
        default=10,
        help_text="Nombre de QCM qu'un individuel sans abonnement/pack peut passer gratuitement par jour."
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def instance(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Paramètres de la plateforme"