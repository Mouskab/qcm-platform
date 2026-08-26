# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Organisation, ProfilCreateur, GroupeOrganisation


# core/forms.py — mets à jour InscriptionForm

class InscriptionForm(UserCreationForm):
    ROLES_AUTORISES = [
        (Utilisateur.Role.INDIVIDUEL, "Candidat individuel"),
        (Utilisateur.Role.ADMIN_ORG, "Administrateur d'organisation"),
    ]

    email = forms.EmailField(required=True, label="Adresse e-mail")
    telephone = forms.CharField(required=False, label="Téléphone")
    role = forms.ChoiceField(choices=ROLES_AUTORISES, label="Je m'inscris en tant que")
    nom_organisation = forms.CharField(
        required=False, label="Nom de votre organisation",
        help_text="Requis uniquement si vous créez un compte Administrateur d'organisation."
    )
    accepte_cgu = forms.BooleanField(
        required=True,
        label='J\'accepte les <a href="/legal/cgu/" target="_blank">conditions générales d\'utilisation</a> et la <a href="/legal/confidentialite/" target="_blank">politique de confidentialité</a>.',
    )

    class Meta:
        model = Utilisateur
        fields = ["username", "email", "role", "telephone", "password1", "password2"]

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        nom_organisation = cleaned_data.get("nom_organisation")

        if role == Utilisateur.Role.ADMIN_ORG and not nom_organisation:
            self.add_error("nom_organisation", "Le nom de l'organisation est requis pour ce rôle.")

        return cleaned_data


class AjoutMembreForm(forms.ModelForm):
    ROLES_MEMBRE_BASE = [
        (Utilisateur.Role.APPRENANT, "Apprenant"),
        (Utilisateur.Role.CREATEUR, "Créateur de contenu"),
    ]
    ROLE_ADMIN = (Utilisateur.Role.ADMIN_ORG, "Administrateur")

    role = forms.ChoiceField(choices=ROLES_MEMBRE_BASE, label="Rôle")

    class Meta:
        model = Utilisateur
        fields = ["username", "email", "role", "telephone"]

    def __init__(self, *args, organisation=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Le rôle Administrateur n'est proposé que si l'organisation autorise
        # plusieurs admins — sinon on ne montre que Apprenant/Créateur.
        if organisation and organisation.autorise_multi_admin:
            self.fields["role"].choices = self.ROLES_MEMBRE_BASE + [self.ROLE_ADMIN]




class OrganisationBrandingForm(forms.ModelForm):
    class Meta:
        model = Organisation
        fields = ["nom_affiche", "logo", "couleur_primaire", "couleur_secondaire", "autorise_multi_admin"]
        widgets = {
            "couleur_primaire": forms.TextInput(attrs={"type": "color"}),
            "couleur_secondaire": forms.TextInput(attrs={"type": "color"}),
        }
        labels = {
            "autorise_multi_admin": "Autoriser plusieurs administrateurs pour mon organisation",
        }

class ProfilForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ["username", "email", "telephone"]

class GroupeForm(forms.ModelForm):
    class Meta:
        model = GroupeOrganisation
        fields = ["nom", "description", "membres"]
        widgets = {
            "membres": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, organisation=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organisation:
            self.fields["membres"].queryset = Utilisateur.objects.filter(organisation=organisation)