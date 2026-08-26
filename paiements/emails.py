# paiements/emails.py
from django.core.mail import send_mail
from django.conf import settings
from core.models import Utilisateur


def notifier_admin_nouveau_paiement(paiement):
    """Alerte le(s) Super Admin(s) de la plateforme dès qu'une preuve de
    paiement est déposée, pour un traitement rapide."""
    cible = paiement.abonnement.plan.nom if paiement.abonnement else paiement.achat_pack.pack.nom

    emails_admins = list(
        Utilisateur.objects.filter(role=Utilisateur.Role.SUPER_ADMIN, email__isnull=False)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    if not emails_admins:
        return

    lien_admin = f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/admin/paiements/paiement/{paiement.id}/change/"

    send_mail(
        subject=f"💰 Nouveau paiement à valider — {paiement.montant} {paiement.devise}",
        message=(
            f"Un candidat vient de déposer une preuve de paiement.\n\n"
            f"Candidat : {paiement.utilisateur.username}\n"
            f"Montant : {paiement.montant} {paiement.devise}\n"
            f"Pour : {cible}\n"
            f"Mode : {paiement.get_mode_display()}\n"
            f"Référence : {paiement.reference_interne}\n\n"
            f"Traiter maintenant : {lien_admin}\n\n"
            f"Merci de valider rapidement pour ne pas retarder l'accès du candidat."
        ),
        from_email=None,
        recipient_list=emails_admins,
        fail_silently=True,
    )