# tentatives/services.py
from django.db import transaction
from django.utils import timezone
from qcm.models import QCM, Question
from .models import Tentative, ReponseUtilisateur


class LimiteTentativesAtteinte(Exception):
    """Levée quand l'utilisateur a épuisé ses tentatives autorisées pour ce QCM"""
    pass


def corriger_question_choix_unique(question, reponses_ids_choisies):
    bonne_reponse = question.reponses.filter(est_correcte=True).first()
    if not bonne_reponse:
        return 0
    if len(reponses_ids_choisies) == 1 and reponses_ids_choisies[0] == bonne_reponse.id:
        return question.points
    return 0


def corriger_question_choix_multiple(question, reponses_ids_choisies):
    bonnes_reponses_ids = set(
        question.reponses.filter(est_correcte=True).values_list("id", flat=True)
    )
    choisies_ids = set(reponses_ids_choisies)
    mode = question.qcm.mode_scoring_choix_multiple

    if mode == QCM.ModeScoring.TOUT_OU_RIEN:
        return question.points if choisies_ids == bonnes_reponses_ids else 0

    if mode == QCM.ModeScoring.POINTS_PARTIELS:
        nb_bonnes_cochees = len(choisies_ids & bonnes_reponses_ids)
        nb_erreurs = len(choisies_ids - bonnes_reponses_ids)
        nb_total_bonnes = len(bonnes_reponses_ids) or 1

        if question.qcm.penalise_erreurs_choix_multiple:
            score_ratio = max(0, (nb_bonnes_cochees - nb_erreurs)) / nb_total_bonnes
        else:
            score_ratio = nb_bonnes_cochees / nb_total_bonnes

        return round(question.points * score_ratio, 2)

    return 0


def corriger_reponse(question, reponses_ids_choisies, texte_saisi):
    if question.type_question == Question.TypeQuestion.CHOIX_UNIQUE:
        return corriger_question_choix_unique(question, reponses_ids_choisies), False
    if question.type_question == Question.TypeQuestion.CHOIX_MULTIPLE:
        return corriger_question_choix_multiple(question, reponses_ids_choisies), False
    if question.type_question == Question.TypeQuestion.TEXTE_LIBRE:
        return None, True
    return 0, False


def soumettre_tentative(qcm, utilisateur, reponses_data):
    """
    Point d'entrée unique, utilisé par l'API ET par le web.
    Protégé par une transaction + verrou (select_for_update) pour éviter
    qu'une double soumission simultanée ne contourne la limite de tentatives.
    Pleinement effectif sous PostgreSQL ; SQLite ignore le verrou sans échouer.
    """
    with transaction.atomic():
        nb_tentatives_existantes = Tentative.objects.select_for_update().filter(
            qcm=qcm, utilisateur=utilisateur
        ).count()

        if qcm.tentatives_autorisees != 0 and nb_tentatives_existantes >= qcm.tentatives_autorisees:
            raise LimiteTentativesAtteinte()

        tentative = Tentative.objects.create(qcm=qcm, utilisateur=utilisateur, statut=Tentative.Statut.EN_COURS)

        score_obtenu = 0
        score_max = 0
        necessite_correction_globale = False

        for reponse_data in reponses_data:
            question = Question.objects.get(id=reponse_data["question_id"], qcm=qcm)
            score_max += question.points

            points, necessite_correction = corriger_reponse(
                question, reponse_data.get("reponses_ids", []), reponse_data.get("texte_saisi", "")
            )

            reponse_utilisateur = ReponseUtilisateur.objects.create(
                tentative=tentative,
                question=question,
                texte_saisi=reponse_data.get("texte_saisi", ""),
                points_attribues=points,
            )
            if reponse_data.get("reponses_ids"):
                reponse_utilisateur.reponses_choisies.set(reponse_data["reponses_ids"])

            if necessite_correction:
                necessite_correction_globale = True
            elif points is not None:
                score_obtenu += points

        tentative.date_fin = timezone.now()
        tentative.score_max = score_max
        tentative.score_obtenu = score_obtenu
        tentative.statut = (
            Tentative.Statut.ATTENTE_CORRECTION if necessite_correction_globale
            else Tentative.Statut.CORRIGEE_AUTO
        )
        tentative.save()
        return tentative


def calculer_stats_organisation(organisation):
    """
    Agrège les statistiques pédagogiques d'une organisation :
    performance par membre, par thématique, moyenne générale.
    """
    tentatives = Tentative.objects.filter(
        qcm__organisation=organisation,
        score_max__gt=0,
    ).select_related("utilisateur", "qcm__thematique")

    stats_par_membre = {}
    stats_par_thematique = {}
    somme_generale = 0
    nb_generale = 0

    for tentative in tentatives:
        pourcentage = (tentative.score_obtenu or 0) / tentative.score_max * 100
        somme_generale += pourcentage
        nb_generale += 1

        membre_id = tentative.utilisateur_id
        if membre_id not in stats_par_membre:
            stats_par_membre[membre_id] = {
                "utilisateur": tentative.utilisateur,
                "nb_tentatives": 0,
                "somme_pourcentage": 0,
                "derniere_activite": tentative.date_debut,
            }
        m = stats_par_membre[membre_id]
        m["nb_tentatives"] += 1
        m["somme_pourcentage"] += pourcentage
        if tentative.date_debut > m["derniere_activite"]:
            m["derniere_activite"] = tentative.date_debut

        nom_thematique = tentative.qcm.thematique.nom
        if nom_thematique not in stats_par_thematique:
            stats_par_thematique[nom_thematique] = {
                "nom": nom_thematique,
                "nb_tentatives": 0,
                "somme_pourcentage": 0,
            }
        t = stats_par_thematique[nom_thematique]
        t["nb_tentatives"] += 1
        t["somme_pourcentage"] += pourcentage

    membres = [
        {
            "utilisateur": data["utilisateur"],
            "nb_tentatives": data["nb_tentatives"],
            "moyenne": round(data["somme_pourcentage"] / data["nb_tentatives"], 1),
            "derniere_activite": data["derniere_activite"],
        }
        for data in stats_par_membre.values()
    ]
    membres.sort(key=lambda m: m["moyenne"], reverse=True)

    thematiques = [
        {
            "nom": data["nom"],
            "nb_tentatives": data["nb_tentatives"],
            "moyenne": round(data["somme_pourcentage"] / data["nb_tentatives"], 1),
        }
        for data in stats_par_thematique.values()
    ]
    thematiques.sort(key=lambda t: t["moyenne"])

    moyenne_generale = round(somme_generale / nb_generale, 1) if nb_generale else None

    return {
        "membres": membres,
        "thematiques": thematiques,
        "moyenne_generale": moyenne_generale,
        "nb_tentatives_total": nb_generale,
    }


def evolution_tentatives_qcm(user, qcm):
    """Historique des tentatives de CET utilisateur sur CE QCM, avec tendance."""
    tentatives = Tentative.objects.filter(
        utilisateur=user, qcm=qcm, score_max__isnull=False, score_max__gt=0
    ).exclude(statut=Tentative.Statut.ATTENTE_CORRECTION).order_by("date_debut")

    historique = []
    pourcentage_precedent = None

    for tentative in tentatives:
        pourcentage = round((tentative.score_obtenu or 0) / tentative.score_max * 100, 1)

        if pourcentage_precedent is None:
            tendance = "premiere"
        elif pourcentage > pourcentage_precedent:
            tendance = "hausse"
        elif pourcentage < pourcentage_precedent:
            tendance = "baisse"
        else:
            tendance = "stable"

        historique.append({
            "tentative_id": tentative.id,
            "date": tentative.date_debut,
            "score_obtenu": tentative.score_obtenu,
            "score_max": tentative.score_max,
            "pourcentage": pourcentage,
            "tendance": tendance,
        })
        pourcentage_precedent = pourcentage

    meilleur = max((h["pourcentage"] for h in historique), default=None)

    return {
        "historique": historique,
        "meilleur_pourcentage": meilleur,
        "nb_tentatives": len(historique),
    }


def calculer_classement_qcm(qcm, utilisateur_courant=None, limite=20):
    """Classement des utilisateurs sur un QCM, par meilleur score obtenu."""
    tentatives = Tentative.objects.filter(
        qcm=qcm,
        score_obtenu__isnull=False,
        score_max__gt=0,
    ).exclude(
        statut=Tentative.Statut.ATTENTE_CORRECTION
    ).select_related("utilisateur")

    meilleures_par_utilisateur = {}
    for tentative in tentatives:
        pourcentage = tentative.score_obtenu / tentative.score_max * 100
        uid = tentative.utilisateur_id
        if uid not in meilleures_par_utilisateur or pourcentage > meilleures_par_utilisateur[uid]["pourcentage"]:
            meilleures_par_utilisateur[uid] = {
                "utilisateur": tentative.utilisateur,
                "pourcentage": round(pourcentage, 1),
                "score_obtenu": tentative.score_obtenu,
                "score_max": tentative.score_max,
            }

    classement = sorted(meilleures_par_utilisateur.values(), key=lambda x: x["pourcentage"], reverse=True)

    rang = 0
    dernier_pourcentage = None
    for i, entree in enumerate(classement):
        if entree["pourcentage"] != dernier_pourcentage:
            rang = i + 1
            dernier_pourcentage = entree["pourcentage"]
        entree["rang"] = rang

    rang_utilisateur_courant = None
    if utilisateur_courant:
        for entree in classement:
            if entree["utilisateur"].id == utilisateur_courant.id:
                rang_utilisateur_courant = entree["rang"]
                break

    return {
        "classement": classement[:limite],
        "nb_participants": len(classement),
        "rang_utilisateur_courant": rang_utilisateur_courant,
    }