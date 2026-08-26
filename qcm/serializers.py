# qcm/serializers.py
from rest_framework import serializers
from .models import Thematique, QCM, Question, Reponse


class ReponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reponse
        fields = ["id", "texte", "est_correcte", "ordre"]


class ReponseSerializerSansCorrection(serializers.ModelSerializer):
    """Utilisé pour l'apprenant AVANT de passer le QCM : on ne doit jamais
    révéler quelle réponse est correcte avant la soumission."""
    class Meta:
        model = Reponse
        fields = ["id", "texte", "ordre"]  # pas de "est_correcte" !


class QuestionSerializer(serializers.ModelSerializer):
    """Pour le créateur/admin : vue complète, avec les bonnes réponses visibles"""
    reponses = ReponseSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id", "enonce", "image", "type_question",
            "points", "ordre", "reponses"
        ]


class QuestionSerializerPourApprenant(serializers.ModelSerializer):
    """Pour l'apprenant qui passe le QCM : pas de indice sur la bonne réponse"""
    reponses = ReponseSerializerSansCorrection(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id", "enonce", "image", "type_question",
            "points", "ordre", "reponses"
        ]


class ThematiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thematique
        fields = ["id", "nom", "description", "organisation"]


class QCMSerializer(serializers.ModelSerializer):
    """Vue complète (créateur/admin) : questions avec bonnes réponses visibles"""
    questions = QuestionSerializer(many=True, read_only=True)
    thematique = ThematiqueSerializer(read_only=True)

    class Meta:
        model = QCM
        fields = [
            "id", "titre", "description", "thematique", "organisation",
            "createur", "est_public", "duree_minutes", "tentatives_autorisees",
            "mode_scoring_choix_multiple", "affichage_score",
            "date_creation", "date_publication", "actif", "questions"
        ]


class QCMSerializerPourApprenant(serializers.ModelSerializer):
    """Vue apprenant : questions SANS les bonnes réponses"""
    questions = QuestionSerializerPourApprenant(many=True, read_only=True)
    thematique = ThematiqueSerializer(read_only=True)

    class Meta:
        model = QCM
        fields = [
            "id", "titre", "description", "thematique",
            "duree_minutes", "tentatives_autorisees", "questions"
        ]


class QCMListSerializer(serializers.ModelSerializer):
    """Vue légère pour lister les QCM (catalogue), sans le détail des questions"""
    thematique = ThematiqueSerializer(read_only=True)

    class Meta:
        model = QCM
        fields = [
            "id", "titre", "description", "thematique",
            "est_public", "duree_minutes", "date_publication"
        ]