from django.contrib import admin
from .models import PlanAbonnement, Abonnement


@admin.register(PlanAbonnement)
class PlanAbonnementAdmin(admin.ModelAdmin):
    list_display = ("nom", "type_cible", "duree", "prix", "devise", "actif")
    list_filter = ("type_cible", "duree", "actif")


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ("plan", "organisation", "utilisateur", "statut", "date_debut", "date_fin")
    list_filter = ("statut", "plan")

# abonnements/admin.py (ajouter)
from .models import Pack, AchatPack


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ("nom", "thematique", "prix", "devise", "actif")
    list_filter = ("actif", "thematique")


@admin.register(AchatPack)
class AchatPackAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "pack", "statut", "date_achat")
    list_filter = ("statut",)