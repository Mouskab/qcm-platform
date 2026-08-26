# core/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Utilisateur, Organisation, ProfilCreateur


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = [
            "id", "nom", "nom_affiche", "logo",
            "couleur_primaire", "couleur_secondaire",
            "autorise_multi_admin", "actif"
        ]


class UtilisateurSerializer(serializers.ModelSerializer):
    organisation = OrganisationSerializer(read_only=True)

    class Meta:
        model = Utilisateur
        fields = [
            "id", "username", "email", "role",
            "organisation", "telephone"
        ]


class InscriptionSerializer(serializers.ModelSerializer):
    """Utilisé uniquement pour la création de compte (inscription)"""
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = Utilisateur
        fields = ["username", "email", "password", "role", "telephone"]

    def create(self, validated_data):
        # On ne peut pas juste faire Utilisateur.objects.create(**validated_data)
        # car le mot de passe doit être hashé, pas stocké en clair
        user = Utilisateur.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            role=validated_data.get("role", Utilisateur.Role.INDIVIDUEL),
            telephone=validated_data.get("telephone", ""),
        )
        return user