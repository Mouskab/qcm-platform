# qcm/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import QCM, Question, Reponse


class QCMForm(forms.ModelForm):
    class Meta:
        model = QCM
        fields = [
            "titre", "description", "thematique", "duree_minutes",
            "tentatives_autorisees", "mode_scoring_choix_multiple",
            "penalise_erreurs_choix_multiple", "affichage_score",
            "est_public", "actif", "groupes",
        ]
        widgets = {
            "groupes": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, organisation=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organisation:
            self.fields["groupes"].queryset = organisation.groupes.all()
        else:
            # Super Admin (pas d'organisation) ou aucune org fournie :
            # pas de groupes à proposer, on vide la liste plutôt que de
            # risquer d'exposer les groupes de toutes les organisations.
            self.fields["groupes"].queryset = self.fields["groupes"].queryset.none()
        self.fields["groupes"].required = False


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["enonce", "image", "type_question", "points"]


ReponseFormSet = inlineformset_factory(
    Question, Reponse,
    fields=["texte", "est_correcte"],
    extra=4, can_delete=True
)


class ImportQuestionsForm(forms.Form):
    fichier = forms.FileField(
        label="Fichier Excel (.xlsx)",
        help_text="Téléchargez le modèle ci-dessous, remplissez-le, puis importez-le ici."
    )