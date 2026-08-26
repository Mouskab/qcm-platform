# tentatives/models.py
from django.db import models
from core.models import Utilisateur
from qcm.models import QCM, Question, Reponse


class Tentative(models.Model):
    class Statut(models.TextChoices):
        EN_COURS = "en_cours", "En cours"
        CORRIGEE_AUTO = "corrigee_auto", "Corrigée automatiquement"
        ATTENTE_CORRECTION = "attente_correction", "En attente de correction manuelle"
        CORRIGEE_COMPLETE = "corrigee_complete", "Corrigée complètement"

    qcm = models.ForeignKey(QCM, on_delete=models.CASCADE, related_name="tentatives")
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="tentatives")
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_COURS)
    score_obtenu = models.FloatField(null=True, blank=True)
    score_max = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.utilisateur} - {self.qcm} ({self.date_debut.date()})"


class ReponseUtilisateur(models.Model):
    tentative = models.ForeignKey(Tentative, on_delete=models.CASCADE, related_name="reponses_utilisateur")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    # Pour choix_unique / choix_multiple
    reponses_choisies = models.ManyToManyField(Reponse, blank=True)

    # Pour texte_libre
    texte_saisi = models.TextField(blank=True)
    points_attribues = models.FloatField(null=True, blank=True)  # rempli après correction manuelle
    corrige_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="corrections_effectuees"
    )
    date_correction = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Réponse à '{self.question}' par {self.tentative.utilisateur}"