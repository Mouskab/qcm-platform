# qcm/models.py
from django.db import models
from django.core.validators import FileExtensionValidator
from core.models import Organisation, Utilisateur
from core.validators import valider_taille_image, valider_contenu_image


class Thematique(models.Model):
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE,
        related_name="thematiques", null=True, blank=True
    )

    def __str__(self):
        return self.nom


class QCM(models.Model):
    class ModeScoring(models.TextChoices):
        TOUT_OU_RIEN = "tout_ou_rien", "Tout ou rien"
        POINTS_PARTIELS = "points_partiels", "Points partiels"

    class AffichageScore(models.TextChoices):
        IMMEDIAT_PARTIEL = "immediat_partiel", "Immédiat (partiel si texte libre)"
        MASQUE_JUSQUA_CORRECTION = "masque", "Masqué jusqu'à correction complète"

    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thematique = models.ForeignKey(Thematique, on_delete=models.CASCADE, related_name="qcms")
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE,
        related_name="qcms", null=True, blank=True
    )
    createur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, related_name="qcms_crees"
    )
    groupes = models.ManyToManyField(
        "core.GroupeOrganisation", related_name="qcms", blank=True,
        help_text="Si aucun groupe n'est sélectionné, le QCM est visible par toute l'organisation."
    )

    est_public = models.BooleanField(default=False)
    duree_minutes = models.PositiveIntegerField(help_text="Durée globale du QCM en minutes")
    tentatives_autorisees = models.PositiveIntegerField(
        default=1, help_text="0 = illimité"
    )
    mode_scoring_choix_multiple = models.CharField(
        max_length=20, choices=ModeScoring.choices, default=ModeScoring.TOUT_OU_RIEN
    )
    penalise_erreurs_choix_multiple = models.BooleanField(
        default=False,
        help_text="Si activé, chaque mauvaise réponse cochée retire des points (mode points_partiels uniquement)"
    )
    affichage_score = models.CharField(
        max_length=20, choices=AffichageScore.choices, default=AffichageScore.IMMEDIAT_PARTIEL
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_publication = models.DateTimeField(null=True, blank=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.titre


class Question(models.Model):
    class TypeQuestion(models.TextChoices):
        CHOIX_UNIQUE = "choix_unique", "Choix unique (radio)"
        CHOIX_MULTIPLE = "choix_multiple", "Choix multiple (checkbox)"
        TEXTE_LIBRE = "texte_libre", "Texte libre"

    qcm = models.ForeignKey(QCM, on_delete=models.CASCADE, related_name="questions")
    enonce = models.TextField()
    image = models.ImageField(
        upload_to="questions/images/",
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"]),
            valider_taille_image,
            valider_contenu_image,
        ],
    )
    type_question = models.CharField(max_length=20, choices=TypeQuestion.choices)
    points = models.PositiveIntegerField(default=1, help_text="Poids / difficulté")
    ordre = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.enonce[:50]


class Reponse(models.Model):
    """Utilisé uniquement pour les questions choix_unique et choix_multiple"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="reponses")
    texte = models.CharField(max_length=500)
    est_correcte = models.BooleanField(default=False)
    ordre = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.texte