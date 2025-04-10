import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_slack_alert(message: str, username="🛑 COGU Incident Bot"):
    if not settings.SLACK_ALERT_WEBHOOK:
        logger.warning("SLACK_ALERT_WEBHOOK n’est pas configuré.")
        return

    try:
        payload = {
            "text": message,
            "username": username,
            "icon_emoji": ":rotating_light:"
        }
        resp = requests.post(
            settings.SLACK_ALERT_WEBHOOK,
            json=payload,
            timeout=5
        )
        resp.raise_for_status()
        logger.info("✅ Alerte Slack envoyée.")
    except Exception as e:
        logger.error(f"Erreur d’envoi Slack : {e}")
