from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Organisation, Utilisateur, ProfilCreateur,ParametrePlateforme
from .models import GroupeOrganisation


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("nom", "nom_affiche", "autorise_multi_admin", "actif", "date_creation")
    list_filter = ("actif", "autorise_multi_admin")
    search_fields = ("nom", "nom_affiche")


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    # On étend l'admin par défaut de Django pour ajouter nos champs custom
    list_display = ("username", "email", "role", "organisation", "is_staff")
    list_filter = ("role", "organisation", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Informations QCM Platform", {"fields": ("role", "organisation", "telephone")}),
    )


@admin.register(ProfilCreateur)
class ProfilCreateurAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "statut_remuneration", "taux_par_question", "actif")
    list_filter = ("statut_remuneration", "actif")



@admin.register(ParametrePlateforme)
class ParametrePlateformeAdmin(admin.ModelAdmin):
    list_display = ("quota_qcm_gratuit_par_jour",)

    def has_add_permission(self, request):
        # Empêche de créer une 2e instance depuis l'admin — le singleton existe déjà ou se crée tout seul
        return not ParametrePlateforme.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GroupeOrganisation)
class GroupeOrganisationAdmin(admin.ModelAdmin):
    list_display = ("nom", "organisation", "date_creation")
    list_filter = ("organisation",)
    filter_horizontal = ("membres",)