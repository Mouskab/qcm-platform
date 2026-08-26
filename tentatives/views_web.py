# tentatives/views_web.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, DetailView
from django.http import Http404
from django.utils import timezone

from qcm.models import QCM, Question
from core.services import (
    verifier_acces_qcm, quota_restant_aujourdhui, possede_abonnement_actif,
    qcm_queryset_visible_pour, qcm_visible_pour,
)
from core.emails import envoyer_notification_correction
from .models import Tentative, ReponseUtilisateur
from .services import soumettre_tentative, LimiteTentativesAtteinte, evolution_tentatives_qcm
from .services import calculer_classement_qcm
from django.db.models import Q
from qcm.models import Thematique


class QCMCatalogueWebView(LoginRequiredMixin, ListView):
    template_name = "tentatives/catalogue.html"
    context_object_name = "qcms"
    paginate_by = 12

    def get_queryset(self):
        queryset = qcm_queryset_visible_pour(self.request.user).select_related("thematique")

        recherche = self.request.GET.get("q", "").strip()
        if recherche:
            queryset = queryset.filter(
                Q(titre__icontains=recherche) | Q(description__icontains=recherche)
            )

        thematique_id = self.request.GET.get("thematique")
        if thematique_id:
            queryset = queryset.filter(thematique_id=thematique_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.organisation_id and not possede_abonnement_actif(user):
            context["quota_restant"] = quota_restant_aujourdhui(user)

        # Liste des thématiques réellement présentes dans les QCM visibles
        # par cet utilisateur, pour peupler le filtre déroulant.
        context["thematiques"] = Thematique.objects.filter(
            qcms__in=qcm_queryset_visible_pour(user)
        ).distinct()
        context["recherche_actuelle"] = self.request.GET.get("q", "")
        context["thematique_actuelle"] = self.request.GET.get("thematique", "")
        return context


class PasserQCMView(LoginRequiredMixin, View):
    def get(self, request, pk):
        qcm = get_object_or_404(QCM, pk=pk, actif=True)
        if not qcm_visible_pour(request.user, qcm):
            raise Http404

        autorise, motif = verifier_acces_qcm(request.user, qcm=qcm)
        if not autorise:
            return render(request, "tentatives/acces_refuse.html", {"motif": motif})

        questions = qcm.questions.prefetch_related("reponses").order_by("ordre")
        return render(request, "tentatives/passer.html", {"qcm": qcm, "questions": questions})

    def post(self, request, pk):
        qcm = get_object_or_404(QCM, pk=pk, actif=True)
        if not qcm_visible_pour(request.user, qcm):
            raise Http404

        autorise, motif = verifier_acces_qcm(request.user, qcm=qcm)
        if not autorise:
            return render(request, "tentatives/acces_refuse.html", {"motif": motif})

        questions = qcm.questions.all()
        reponses_data = []

        for question in questions:
            if question.type_question == Question.TypeQuestion.CHOIX_UNIQUE:
                valeur = request.POST.get(f"question_{question.id}")
                reponses_data.append({
                    "question_id": question.id,
                    "reponses_ids": [int(valeur)] if valeur else []
                })
            elif question.type_question == Question.TypeQuestion.CHOIX_MULTIPLE:
                valeurs = request.POST.getlist(f"question_{question.id}")
                reponses_data.append({
                    "question_id": question.id,
                    "reponses_ids": [int(v) for v in valeurs]
                })
            else:
                texte = request.POST.get(f"question_{question.id}", "")
                reponses_data.append({"question_id": question.id, "texte_saisi": texte})

        try:
            tentative = soumettre_tentative(qcm, request.user, reponses_data)
        except LimiteTentativesAtteinte:
            return render(request, "tentatives/limite_atteinte.html", {"qcm": qcm})

        return redirect("resultat-tentative-web", pk=tentative.pk)


class MesResultatsListView(LoginRequiredMixin, ListView):
    template_name = "tentatives/mes_resultats.html"
    context_object_name = "tentatives"
    paginate_by = 15

    def get_queryset(self):
        return Tentative.objects.filter(
            utilisateur=self.request.user
        ).select_related("qcm").order_by("-date_debut")


class ResultatTentativeDetailView(LoginRequiredMixin, DetailView):
    model = Tentative
    template_name = "tentatives/resultat_detail.html"
    context_object_name = "tentative"

    def get_queryset(self):
        return Tentative.objects.filter(utilisateur=self.request.user)


class EvolutionQcmWebView(LoginRequiredMixin, View):
    def get(self, request, qcm_id):
        qcm = get_object_or_404(QCM, id=qcm_id)
        donnees = evolution_tentatives_qcm(request.user, qcm)
        return render(request, "tentatives/evolution.html", {"qcm": qcm, **donnees})


class EstCorrecteurMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ["createur", "admin_org", "super_admin"]


class ATCorrigerListView(LoginRequiredMixin, EstCorrecteurMixin, ListView):
    template_name = "tentatives/a_corriger_liste.html"
    context_object_name = "tentatives"

    def get_queryset(self):
        user = self.request.user
        queryset = Tentative.objects.filter(
            statut=Tentative.Statut.ATTENTE_CORRECTION
        ).select_related("qcm", "utilisateur")

        if user.role != "super_admin":
            queryset = queryset.filter(qcm__organisation=user.organisation)

        return queryset.order_by("date_debut")


class CorrigerTentativeView(LoginRequiredMixin, EstCorrecteurMixin, View):
    def get(self, request, pk):
        tentative = get_object_or_404(Tentative, pk=pk, statut=Tentative.Statut.ATTENTE_CORRECTION)
        self._verifier_acces(request, tentative)

        reponses_texte = tentative.reponses_utilisateur.filter(
            question__type_question="texte_libre"
        ).select_related("question")

        return render(request, "tentatives/corriger.html", {
            "tentative": tentative,
            "reponses_texte": reponses_texte,
        })

    def post(self, request, pk):
        tentative = get_object_or_404(Tentative, pk=pk, statut=Tentative.Statut.ATTENTE_CORRECTION)
        self._verifier_acces(request, tentative)

        reponses_texte = tentative.reponses_utilisateur.filter(question__type_question="texte_libre")

        for reponse in reponses_texte:
            points = request.POST.get(f"points_{reponse.id}")
            if points is not None and points != "":
                reponse.points_attribues = float(points)
                reponse.corrige_par = request.user
                reponse.date_correction = timezone.now()
                reponse.save()

        encore_non_corrigees = tentative.reponses_utilisateur.filter(
            question__type_question="texte_libre", points_attribues__isnull=True
        ).exists()

        if not encore_non_corrigees:
            score_total = sum(r.points_attribues or 0 for r in tentative.reponses_utilisateur.all())
            tentative.score_obtenu = score_total
            tentative.statut = Tentative.Statut.CORRIGEE_COMPLETE
            tentative.save()
            envoyer_notification_correction(tentative)
            return redirect("a-corriger-liste-web")

        return redirect("corriger-tentative-web", pk=tentative.pk)

    def _verifier_acces(self, request, tentative):
        if request.user.role != "super_admin" and tentative.qcm.organisation_id != request.user.organisation_id:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Cette tentative n'appartient pas à votre organisation.")




class ClassementQCMView(LoginRequiredMixin, View):
    def get(self, request, pk):
        qcm = get_object_or_404(QCM, pk=pk, actif=True)
        if not qcm_visible_pour(request.user, qcm):
            raise Http404

        data = calculer_classement_qcm(qcm, utilisateur_courant=request.user)
        return render(request, "tentatives/classement.html", {"qcm": qcm, **data})