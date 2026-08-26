# paiements/admin.py
from django.contrib import admin
from .models import Paiement
from .services import confirmer_paiement


@admin.action(description="Valider ce(s) paiement(s) (active l'abonnement/pack + envoie le reçu)")
def valider_paiements(modeladmin, request, queryset):
    nb_valides = 0
    for paiement in queryset.filter(statut=Paiement.Statut.EN_ATTENTE):
        confirmer_paiement(
            paiement.reference_interne, "valide", {"validation": "manuelle_admin"},
            valide_par=request.user
        )
        nb_valides += 1
    modeladmin.message_user(request, f"{nb_valides} paiement(s) validé(s) et accès activé(s).")


@admin.action(description="Refuser ce(s) paiement(s)")
def refuser_paiements(modeladmin, request, queryset):
    nb_refuses = 0
    for paiement in queryset.filter(statut=Paiement.Statut.EN_ATTENTE):
        confirmer_paiement(paiement.reference_interne, "refuse", {"validation": "manuelle_admin"}, valide_par=request.user)
        nb_refuses += 1
    modeladmin.message_user(request, f"{nb_refuses} paiement(s) refusé(s).")


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "montant", "devise", "mode", "statut", "fournisseur", "date_creation")
    list_filter = ("mode", "statut", "fournisseur")
    readonly_fields = ("reponse_fournisseur", "reference_interne")
    search_fields = ("utilisateur__username", "reference_transaction")
    actions = [valider_paiements, refuser_paiements]