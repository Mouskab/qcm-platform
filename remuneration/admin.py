from django.contrib import admin
from .models import RemunerationCreateur, QuestionRemuneree


class QuestionRemunereeInline(admin.TabularInline):
    model = QuestionRemuneree
    extra = 0


@admin.register(RemunerationCreateur)
class RemunerationCreateurAdmin(admin.ModelAdmin):
    list_display = ("profil_createur", "periode_debut", "periode_fin", "montant_calcule", "statut")
    list_filter = ("statut",)
    inlines = [QuestionRemunereeInline]