import requests
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_slack_alert(message: str):
    try:
        if not settings.SLACK_ALERT_WEBHOOK:
            logger.warning("SLACK_ALERT_WEBHOOK non défini")
            return
        requests.post(
            settings.SLACK_ALERT_WEBHOOK,
            json={"text": message, "username": "🛑 COGU Bot", "icon_emoji": ":rotating_light:"},
            timeout=5
        )
        logger.info("✅ Slack alert envoyé")
    except Exception as e:
        logger.error(f"❌ Slack error: {e}")


def send_email_alert(subject, body):
    try:
        if not settings.EMAIL_ALERT_RECEIVERS:
            logger.warning("EMAIL_ALERT_RECEIVERS non défini")
            return
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            settings.EMAIL_ALERT_RECEIVERS,
            fail_silently=False,
        )
        logger.info("✅ Email alert envoyé")
    except Exception as e:
        logger.error(f"❌ Email error: {e}")
