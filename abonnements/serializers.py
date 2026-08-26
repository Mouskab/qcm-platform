# abonnements/serializers.py
from rest_framework import serializers
from .models import PlanAbonnement, Abonnement, Pack


class PlanAbonnementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanAbonnement
        fields = ["id", "nom", "type_cible", "duree", "prix", "devise", "nb_qcm_max", "nb_utilisateurs_max"]


class ThematiqueLegereSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nom = serializers.CharField()


class PackSerializer(serializers.ModelSerializer):
    thematique_nom = serializers.CharField(source="thematique.nom", read_only=True)
    thematique_id = serializers.IntegerField(source="thematique.id", read_only=True)

    class Meta:
        model = Pack
        fields = ["id", "nom", "description", "thematique_id", "thematique_nom", "prix", "devise"]


class AbonnementSerializer(serializers.ModelSerializer):
    plan = PlanAbonnementSerializer(read_only=True)

    class Meta:
        model = Abonnement
        fields = ["id", "plan", "organisation", "utilisateur", "date_debut", "date_fin", "statut", "date_creation"]
        read_only_fields = ["statut", "date_debut", "date_fin"]