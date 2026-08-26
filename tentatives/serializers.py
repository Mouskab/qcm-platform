# tentatives/serializers.py
from rest_framework import serializers
from .models import Tentative, ReponseUtilisateur
from qcm.models import QCM, Question, Reponse


# ---------- Serializers d'ENTRÉE (soumission d'une tentative) ----------

class ReponseUtilisateurEntreeSerializer(serializers.Serializer):
    """Ce que l'apprenant envoie pour UNE question"""
    question_id = serializers.IntegerField()
    reponses_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    texte_saisi = serializers.CharField(required=False, allow_blank=True, default="")


class SoumissionTentativeSerializer(serializers.Serializer):
    """Ce que l'apprenant envoie pour TOUT le QCM"""
    qcm_id = serializers.IntegerField()
    reponses = ReponseUtilisateurEntreeSerializer(many=True)


# ---------- Serializers de SORTIE (résultat d'une tentative) ----------

class ReponseCorrectionSerializer(serializers.ModelSerializer):
    """Une fois la tentative soumise, révéler la bonne réponse ne pose plus
    de risque de triche — utilisé uniquement dans le résultat final."""
    class Meta:
        model = Reponse
        fields = ["id", "texte", "est_correcte"]


class ReponseUtilisateurSortieSerializer(serializers.ModelSerializer):
    """Détail par question, après correction — inclut désormais la liste
    complète des réponses possibles avec leur statut correct/incorrect."""
    question_enonce = serializers.CharField(source="question.enonce", read_only=True)
    question_type = serializers.CharField(source="question.type_question", read_only=True)
    question_points = serializers.IntegerField(source="question.points", read_only=True)
    reponses_choisies = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    reponses_disponibles = serializers.SerializerMethodField()

    def get_reponses_disponibles(self, obj):
        if obj.question.type_question == "texte_libre":
            return []
        return ReponseCorrectionSerializer(obj.question.reponses.all(), many=True).data

    class Meta:
        model = ReponseUtilisateur
        fields = [
            "id", "question", "question_enonce", "question_type", "question_points",
            "reponses_choisies", "reponses_disponibles", "texte_saisi", "points_attribues"
        ]


class QcmResumeSerializer(serializers.ModelSerializer):
    """Version légère du QCM, pour l'affichage dans une liste/résultat de tentative"""
    class Meta:
        model = QCM
        fields = ["id", "titre"]


class TentativeResultatSerializer(serializers.ModelSerializer):
    """Résultat complet renvoyé après soumission ET utilisé pour l'historique"""
    reponses_utilisateur = ReponseUtilisateurSortieSerializer(many=True, read_only=True)
    qcm = QcmResumeSerializer(read_only=True)

    class Meta:
        model = Tentative
        fields = [
            "id", "qcm", "statut", "score_obtenu", "score_max",
            "date_debut", "date_fin", "reponses_utilisateur"
        ]