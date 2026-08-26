# qcm/views.py
# qcm/views.py
from rest_framework import generics, permissions
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404, render
from django.http import Http404, HttpResponse
import openpyxl
from django.db import models

from core.permissions import EstCreateurOuAdminOrg, EstMembreDeLOrganisation, PeutAccederQCM
from core.services import qcm_queryset_visible_pour, qcm_visible_pour
from .models import Thematique, QCM, Question
from .serializers import (
    ThematiqueSerializer, QCMSerializer, QCMSerializerPourApprenant,
    QCMListSerializer, QuestionSerializer
)
from .forms import QCMForm, QuestionForm, ReponseFormSet, ImportQuestionsForm
from .services import importer_questions_depuis_excel


# ============ API (Django REST Framework) ============

class ThematiqueListCreateView(generics.ListCreateAPIView):
    serializer_class = ThematiqueSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), EstCreateurOuAdminOrg()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        return Thematique.objects.filter(
            Q(organisation__isnull=True) | Q(organisation=user.organisation)
        )

    def perform_create(self, serializer):
        organisation = None if self.request.user.role == "super_admin" else self.request.user.organisation
        serializer.save(organisation=organisation)


class QCMListView(generics.ListAPIView):
    serializer_class = QCMListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = qcm_queryset_visible_pour(self.request.user)

        recherche = self.request.query_params.get("q", "").strip()
        if recherche:
            queryset = queryset.filter(
                models.Q(titre__icontains=recherche) | models.Q(description__icontains=recherche)
            )

        thematique_id = self.request.query_params.get("thematique")
        if thematique_id:
            queryset = queryset.filter(thematique_id=thematique_id)

        return queryset

class QCMDetailView(generics.RetrieveAPIView):
    """Détail d'un QCM — questions SANS les bonnes réponses (mode apprenant)"""
    serializer_class = QCMSerializerPourApprenant
    permission_classes = [permissions.IsAuthenticated, PeutAccederQCM]
    queryset = QCM.objects.filter(actif=True)

    def get_object(self):
        obj = super().get_object()
        if not qcm_visible_pour(self.request.user, obj):
            raise Http404
        return obj


class QCMCreateView(generics.CreateAPIView):
    serializer_class = QCMSerializer
    permission_classes = [permissions.IsAuthenticated, EstCreateurOuAdminOrg]

    def perform_create(self, serializer):
        organisation = None if self.request.user.role == "super_admin" else self.request.user.organisation
        serializer.save(createur=self.request.user, organisation=organisation)


class QCMUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = QCMSerializer
    permission_classes = [permissions.IsAuthenticated, EstCreateurOuAdminOrg, EstMembreDeLOrganisation]
    queryset = QCM.objects.all()


# ============ Web (dashboard créateur/admin) ============

class EstCreateurOuAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ["createur", "admin_org", "super_admin"]


class QCMListWebView(LoginRequiredMixin, EstCreateurOuAdminMixin, ListView):
    model = QCM
    template_name = "qcm/liste.html"
    context_object_name = "qcms"

    def get_queryset(self):
        user = self.request.user
        if user.role == "super_admin":
            return QCM.objects.all().order_by("-date_creation")
        return QCM.objects.filter(organisation=user.organisation).order_by("-date_creation")


class QCMCreateWebView(LoginRequiredMixin, EstCreateurOuAdminMixin, CreateView):
    model = QCM
    form_class = QCMForm
    template_name = "qcm/formulaire.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user.role != "super_admin":
            kwargs["organisation"] = self.request.user.organisation
        return kwargs

    def form_valid(self, form):
        form.instance.createur = self.request.user
        form.instance.organisation = None if self.request.user.role == "super_admin" else self.request.user.organisation
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("qcm-questions-web", kwargs={"pk": self.object.pk})


class QCMUpdateWebView(LoginRequiredMixin, EstCreateurOuAdminMixin, UpdateView):
    model = QCM
    form_class = QCMForm
    template_name = "qcm/formulaire.html"
    success_url = reverse_lazy("qcm-liste-web")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user.role != "super_admin":
            kwargs["organisation"] = self.request.user.organisation
        return kwargs


class QCMDeleteWebView(LoginRequiredMixin, EstCreateurOuAdminMixin, DeleteView):
    model = QCM
    template_name = "qcm/confirmer_suppression.html"
    success_url = reverse_lazy("qcm-liste-web")


class QCMQuestionsWebView(LoginRequiredMixin, EstCreateurOuAdminMixin, ListView):
    template_name = "qcm/questions.html"
    context_object_name = "questions"

    def get_queryset(self):
        self.qcm = get_object_or_404(QCM, pk=self.kwargs["pk"])
        return self.qcm.questions.all().order_by("ordre")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["qcm"] = self.qcm
        return context


class QuestionCreateWebView(LoginRequiredMixin, EstCreateurOuAdminMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "qcm/question_formulaire.html"

    def dispatch(self, request, *args, **kwargs):
        self.qcm = get_object_or_404(QCM, pk=kwargs["qcm_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["qcm"] = self.qcm
        context["formset"] = ReponseFormSet(self.request.POST or None)
        return context

    def form_valid(self, form):
        form.instance.qcm = self.qcm
        context = self.get_context_data()
        formset = context["formset"]
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return redirect("qcm-questions-web", pk=self.qcm.pk)
        return self.render_to_response(self.get_context_data(form=form))




class QCMImporterQuestionsView(LoginRequiredMixin, EstCreateurOuAdminMixin, View):
    def get(self, request, qcm_pk):
        qcm = get_object_or_404(QCM, pk=qcm_pk)
        return render(request, "qcm/importer_questions.html", {"qcm": qcm, "form": ImportQuestionsForm()})

    def post(self, request, qcm_pk):
        qcm = get_object_or_404(QCM, pk=qcm_pk)
        form = ImportQuestionsForm(request.POST, request.FILES)

        if not form.is_valid():
            return render(request, "qcm/importer_questions.html", {"qcm": qcm, "form": form})

        nb_importees, erreurs = importer_questions_depuis_excel(qcm, request.FILES["fichier"])

        return render(request, "qcm/importer_questions.html", {
            "qcm": qcm,
            "form": ImportQuestionsForm(),
            "nb_importees": nb_importees if not erreurs else None,
            "erreurs": erreurs,
        })


class TelechargerModeleImportView(LoginRequiredMixin, EstCreateurOuAdminMixin, View):
    """Génère et sert un fichier Excel modèle, prêt à remplir."""
    def get(self, request):
        classeur = openpyxl.Workbook()
        feuille = classeur.active
        feuille.title = "Questions"

        entetes = [
            "Question", "Type", "Points",
            "Reponse1", "Reponse1_Correcte", "Reponse2", "Reponse2_Correcte",
            "Reponse3", "Reponse3_Correcte", "Reponse4", "Reponse4_Correcte",
        ]
        feuille.append(entetes)
        feuille.append([
            "Quelle est la capitale du Burkina Faso ?", "choix_unique", 1,
            "Ouagadougou", "Oui", "Bobo-Dioulasso", "Non", "Koudougou", "Non", "", "",
        ])
        feuille.append([
            "Parmi ces pays, lesquels sont limitrophes du Burkina Faso ?", "choix_multiple", 2,
            "Mali", "Oui", "Niger", "Oui", "Sénégal", "Non", "Côte d'Ivoire", "Oui",
        ])
        feuille.append([
            "Expliquez brièvement le rôle du Premier ministre.", "texte_libre", 3,
            "", "", "", "", "", "", "", "",
        ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="modele_import_questions.xlsx"'
        classeur.save(response)
        return response