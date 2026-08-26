# core/validators.py
from django.core.exceptions import ValidationError
from PIL import Image

TAILLE_MAX_MO = 2


def valider_taille_image(fichier):
    taille_mo = fichier.size / (1024 * 1024)
    if taille_mo > TAILLE_MAX_MO:
        raise ValidationError(f"L'image ne doit pas dépasser {TAILLE_MAX_MO} Mo (actuellement {taille_mo:.1f} Mo).")


def valider_contenu_image(fichier):
    """Vérifie que le fichier est RÉELLEMENT une image lisible, pas juste
    un fichier renommé avec une extension .jpg/.png trompeuse."""
    try:
        image = Image.open(fichier)
        image.verify()
    except Exception:
        raise ValidationError("Le fichier fourni n'est pas une image valide.")
    finally:
        fichier.seek(0)  # remet le curseur au début, sinon Django ne peut plus lire le fichier ensuite