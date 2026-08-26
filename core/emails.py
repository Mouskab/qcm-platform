# core/emails.py
from django.core.mail import send_mail


def envoyer_email_bienvenue(utilisateur):
    if not utilisateur.email:
        return
    send_mail(
        subject="Bienvenue sur Zamse !",
        message=(
            f"Bonjour {utilisateur.username},\n\n"
            f"Votre compte Zamse est créé avec succès. Zamse (« apprendre » en mooré) "
            f"vous accompagne dans votre préparation aux concours et examens.\n\n"
            f"Vous pouvez dès maintenant consulter le catalogue de QCM disponibles.\n\n"
            f"Bonne préparation !\nL'équipe Zamse"
        ),
        from_email=None,
        recipient_list=[utilisateur.email],
        fail_silently=True,
    )


def envoyer_recu_paiement(paiement):
    if not paiement.utilisateur.email:
        return
    cible = paiement.abonnement.plan.nom if paiement.abonnement else paiement.achat_pack.pack.nom
    send_mail(
        subject="Reçu de paiement — Zamse",
        message=(
            f"Bonjour {paiement.utilisateur.username},\n\n"
            f"Votre paiement de {paiement.montant} {paiement.devise} pour « {cible} » a bien été validé.\n"
            f"Référence : {paiement.reference_interne}\n\n"
            f"Votre accès est maintenant actif. Merci de votre confiance.\n\n"
            f"L'équipe Zamse"
        ),
        from_email=None,
        recipient_list=[paiement.utilisateur.email],
        fail_silently=True,
    )


def envoyer_notification_correction(tentative):
    if not tentative.utilisateur.email:
        return
    send_mail(
        subject=f"Votre QCM « {tentative.qcm.titre} » a été corrigé",
        message=(
            f"Bonjour {tentative.utilisateur.username},\n\n"
            f"Votre tentative sur « {tentative.qcm.titre} » vient d'être corrigée.\n"
            f"Score final : {tentative.score_obtenu} / {tentative.score_max}\n\n"
            f"Connectez-vous à Zamse pour voir le détail.\n\n"
            f"L'équipe Zamse"
        ),
        from_email=None,
        recipient_list=[tentative.utilisateur.email],
        fail_silently=True,
    )