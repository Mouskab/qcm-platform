from django.contrib import admin
from .models import Tentative, ReponseUtilisateur


class ReponseUtilisateurInline(admin.TabularInline):
    model = ReponseUtilisateur
    extra = 0
    readonly_fields = ("question", "texte_saisi")


@admin.register(Tentative)
class TentativeAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "qcm", "statut", "score_obtenu", "score_max", "date_debut")
    list_filter = ("statut", "qcm")
    search_fields = ("utilisateur__username",)
    inlines = [ReponseUtilisateurInline]