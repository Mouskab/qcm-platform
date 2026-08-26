# paiements/forms.py
from django import forms
from .models import Paiement


class PreuvePaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ["preuve_paiement"]
        widgets = {
            "preuve_paiement": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }