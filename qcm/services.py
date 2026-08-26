# qcm/services.py
import openpyxl
from django.db import transaction
from .models import Question, Reponse

COLONNES_REPONSES_MAX = 6
TYPES_VALIDES = {"choix_unique", "choix_multiple", "texte_libre"}


def _lire_entete(ligne_entete):
    entete = {}
    for idx, cellule in enumerate(ligne_entete):
        if cellule.value:
            entete[str(cellule.value).strip()] = idx
    return entete


def importer_questions_depuis_excel(qcm, fichier):
    """
    Parcourt un fichier Excel et crée les Questions/Réponses pour ce QCM.
    Tout ou rien : si une seule ligne est invalide, rien n'est importé.
    Retourne (nb_questions_importees, liste_erreurs).
    """
    try:
        classeur = openpyxl.load_workbook(fichier, data_only=True)
    except Exception:
        return 0, ["Le fichier n'est pas un fichier Excel (.xlsx) valide."]

    feuille = classeur.active
    lignes = list(feuille.iter_rows())

    if len(lignes) < 2:
        return 0, ["Le fichier est vide ou ne contient pas de questions."]

    entete = _lire_entete(lignes[0])
    colonnes_obligatoires = ["Question", "Type", "Points"]
    manquantes = [c for c in colonnes_obligatoires if c not in entete]
    if manquantes:
        return 0, [f"Colonnes manquantes dans l'en-tête : {', '.join(manquantes)}"]

    erreurs = []
    questions_a_creer = []

    for num_ligne, ligne in enumerate(lignes[1:], start=2):
        def valeur(nom_colonne):
            idx = entete.get(nom_colonne)
            if idx is None or idx >= len(ligne):
                return None
            return ligne[idx].value

        enonce = valeur("Question")
        if not enonce or not str(enonce).strip():
            continue  # ligne vide : fin probable du tableau, on ignore silencieusement

        enonce = str(enonce).strip()
        type_question = str(valeur("Type") or "").strip().lower()
        points_brut = valeur("Points")

        if type_question not in TYPES_VALIDES:
            erreurs.append(f"Ligne {num_ligne} : type '{type_question}' invalide (attendu : choix_unique, choix_multiple ou texte_libre).")
            continue

        try:
            points = int(points_brut)
            if points <= 0:
                raise ValueError
        except (TypeError, ValueError):
            erreurs.append(f"Ligne {num_ligne} : la colonne 'Points' doit être un nombre entier positif.")
            continue

        reponses = []
        if type_question in ("choix_unique", "choix_multiple"):
            for i in range(1, COLONNES_REPONSES_MAX + 1):
                texte_reponse = valeur(f"Reponse{i}")
                if texte_reponse and str(texte_reponse).strip():
                    brut = str(valeur(f"Reponse{i}_Correcte") or "").strip().lower()
                    est_correcte = brut in ("oui", "vrai", "true", "1", "x")
                    reponses.append({"texte": str(texte_reponse).strip(), "est_correcte": est_correcte, "ordre": i})

            if len(reponses) < 2:
                erreurs.append(f"Ligne {num_ligne} : au moins 2 réponses sont requises pour une question à choix.")
                continue

            nb_correctes = sum(1 for r in reponses if r["est_correcte"])
            if nb_correctes == 0:
                erreurs.append(f"Ligne {num_ligne} : aucune réponse marquée correcte (colonne 'Oui').")
                continue
            if type_question == "choix_unique" and nb_correctes > 1:
                erreurs.append(f"Ligne {num_ligne} : une question à choix unique ne peut avoir qu'une seule bonne réponse.")
                continue

        questions_a_creer.append({
            "enonce": enonce, "type_question": type_question, "points": points, "reponses": reponses,
        })

    if erreurs:
        return 0, erreurs
    if not questions_a_creer:
        return 0, ["Aucune question valide trouvée dans le fichier."]

    with transaction.atomic():
        ordre_depart = qcm.questions.count()
        for i, donnees in enumerate(questions_a_creer):
            question = Question.objects.create(
                qcm=qcm, enonce=donnees["enonce"], type_question=donnees["type_question"],
                points=donnees["points"], ordre=ordre_depart + i,
            )
            for r in donnees["reponses"]:
                Reponse.objects.create(question=question, texte=r["texte"], est_correcte=r["est_correcte"], ordre=r["ordre"])

    return len(questions_a_creer), []