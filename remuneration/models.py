# remuneration/models.py
from django.db import models
from core.models import ProfilCreateur, Utilisateur
from qcm.models import Question


class RemunerationCreateur(models.Model):
    """Une ligne = un cycle de rémunération pour un créateur freelance sur une période donnée."""

    class Statut(models.TextChoices):
        CALCULEE = "calculee", "Calculée (en attente de paiement)"
        PAYEE = "payee", "Payée"

    profil_createur = models.ForeignKey(
        ProfilCreateur, on_delete=models.CASCADE, related_name="remunerations"
    )
    periode_debut = models.DateField()
    periode_fin = models.DateField()
    nb_questions_produites = models.PositiveIntegerField()
    montant_calcule = models.DecimalField(max_digits=10, decimal_places=2)
    devise = models.CharField(max_length=10, default="XOF")
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.CALCULEE)

    valide_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="remunerations_validees"
    )
    date_paiement = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profil_createur.utilisateur} - {self.periode_debut} → {self.periode_fin} : {self.montant_calcule} {self.devise}"


class QuestionRemuneree(models.Model):
    """Traçabilité : quelles questions précises sont comptées dans quelle rémunération."""

    remuneration = models.ForeignKey(
        RemunerationCreateur, on_delete=models.CASCADE, related_name="questions_incluses"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("remuneration", "question")  # évite qu'une question soit comptée 2 fois

    def __str__(self):
        return f"{self.question} → {self.remuneration}"