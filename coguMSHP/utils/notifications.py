import os

from django.conf import settings
from django.core.mail import send_mail
from twilio.rest import Client


def send_whatsapp_message(to_number, message_body):
    from cogu.models import WhatsAppMessage
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    from_number = "whatsapp:+14237194194"  # Numéro Twilio Sandbox

    message = client.messages.create(
        from_=from_number,
        body=message_body,
        to=f"whatsapp:{to_number}"
    )

    # Sauvegarder le message
    WhatsAppMessage.objects.create(
        direction="out",
        sender=from_number,
        recipient=to_number,
        body=message_body
    )

    return message.sid


def send_email_alert(subject: str, message: str):
    from coguMSHP.services import logger
    if not settings.EMAIL_ALERT_RECEIVERS:
        logger.warning("EMAIL_ALERT_RECEIVERS non configurés.")
        return

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.EMAIL_ALERT_RECEIVERS,
            fail_silently=False,
        )
        logger.info("✅ Alerte email envoyée avec succès.")
    except Exception as e:
        logger.error(f"❌ Erreur d’envoi de l’alerte email : {e}")
