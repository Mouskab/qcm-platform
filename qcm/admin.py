from django.contrib import admin
from .models import Thematique, QCM, Question, Reponse


@admin.register(Thematique)
class ThematiqueAdmin(admin.ModelAdmin):
    list_display = ("nom", "organisation")
    list_filter = ("organisation",)
    search_fields = ("nom",)


class ReponseInline(admin.TabularInline):
    """Permet d'éditer les réponses directement dans la page de la question"""
    model = Reponse
    extra = 2  # affiche 2 lignes vides par défaut pour ajouter des réponses


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("enonce", "qcm", "type_question", "points", "ordre")
    list_filter = ("type_question", "qcm")
    search_fields = ("enonce",)
    inlines = [ReponseInline]


class QuestionInline(admin.TabularInline):
    """Permet de voir les questions directement dans la page du QCM"""
    model = Question
    extra = 1
    show_change_link = True  # lien pour éditer la question en détail (et ses réponses)


@admin.register(QCM)
class QCMAdmin(admin.ModelAdmin):
    list_display = (
        "titre", "thematique", "organisation", "est_public",
        "mode_scoring_choix_multiple", "penalise_erreurs_choix_multiple", "actif"
    )
    list_filter = ("est_public", "actif", "organisation", "thematique")
    search_fields = ("titre", "description")
    inlines = [QuestionInline]
