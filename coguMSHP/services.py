import logging
import mimetypes
import re
import uuid

import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from coguMSHP.MPIClient import MPIClient
from coguMSHP.utils.notifications import send_email_alert


def synchroniser_avec_mpi(patient_instance):
    mpi_client = MPIClient(
        username="rageuser",
        api_key=settings.MPI_API_KEY,
        mpi_base_url="https://mpici.com"
    )

    patient_data = {
        "nom": patient_instance.nom,
        "prenoms": patient_instance.prenoms,
        "date_naissance": patient_instance.date_naissance.isoformat(),
        "contact": patient_instance.contact,
        "sexe": patient_instance.sexe,
        "num_cmu": patient_instance.num_cmu,
        "cni_num": patient_instance.cni_num,
        "cni_nni": patient_instance.cni_nni,
        "profession": patient_instance.secteur_activite,
        "niveau_etude": patient_instance.niveau_etude,
        # "quartier": patient_instance.quartier,
        # "village": patient_instance.village,
    }

    mpi_response = mpi_client.synchroniser_patient(patient_data)
    return mpi_response.get("upi")


# def synchroniser_avec_mpi(patient_instance):
#     mpi_url = "http://127.0.0.1:8001/mpi/patients/"  # URL du create/update patient MPI
#     token_url = "http://127.0.0.1:8001/api/token/"
#
#     platform_username = "rage"  # doit correspondre au nom d’utilisateur lié à Platform
#     platform_api_key = settings.MPI_API_KEY  # stocké dans .env ou settings sécurisés
#
#     # Étape 1 - Authentifier pour obtenir token
#     response = requests.post(token_url, json={
#         "username": platform_username,
#         "api_key": platform_api_key
#     })
#     if response.status_code != 200:
#         raise Exception("Échec de l'authentification MPI")
#
#     token = response.json()["access"]
#
#     # Étape 2 - Envoi des données du patient
#     payload = {
#         "nom": patient_instance.nom,
#         "prenoms": patient_instance.prenoms,
#         "date_naissance": str(patient_instance.date_naissance),
#         "contact": patient_instance.contact,
#         "sexe": patient_instance.sexe,
#     }
#
#     response = requests.post(mpi_url, json=payload, headers={
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     })
#
#     if response.status_code not in [200, 201]:
#         raise Exception(f"Erreur de communication avec MPI: {response.content}")
#
#     data = response.json()
#     return data.get("upi")

logger = logging.getLogger(__name__)


def get_city_from_text(text):
    from cogu.models import Commune
    # Exemple très simple d'extraction de nom de commune depuis le message
    communes = Commune.objects.all()
    for commune in communes:
        if commune.name.lower() in text.lower():
            return commune
    return None


def geolocate_from_text(message):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": message,
            "format": "json",
            "limit": 1
        }
        headers = {"User-Agent": "IncidentReporterBot/1.0"}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200 and response.json():
            loc = response.json()[0]
            return float(loc["lat"]), float(loc["lon"])
    except Exception as e:
        logger.warning(f"Géolocalisation échouée: {e}")
    return None, None


KEYWORDS_TYPE = {
    'accident': 'Accident',
    'noyade': 'Noyade',
    'intoxication': 'Intoxication',
    'brûlure': 'Brûlure',
    'maladie': 'Maladie',
    'épidémie': 'Épidémie',
}

KEYWORDS_OUTCOME = {
    'mort': 'mort',
    'décès': 'mort',
    'blessé': 'blessure',
    'sauvé': 'sauvé',
}


def send_slack_alert(message):
    try:
        webhook = settings.SLACK_ALERT_WEBHOOK
        requests.post(webhook, json={"text": message}, timeout=5)
    except Exception as e:
        logger.error(f"Erreur envoi Slack : {e}")


def get_location_from_text(text):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": text, "format": "json", "limit": 1}
        headers = {"User-Agent": "cogu-app"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        data = resp.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            from django.contrib.gis.geos import Point
            return Point(lon, lat)
    except Exception as e:
        logger.warning(f"Géocodage échoué pour: {text} | Erreur: {e}")
        return None


def save_twilio_media(request):
    media_count = int(request.POST.get('NumMedia', 0))
    media_files = []

    for i in range(media_count):
        media_url = request.POST.get(f"MediaUrl{i}")
        content_type = request.POST.get(f"MediaContentType{i}")

        if media_url:
            response = requests.get(media_url)
            if response.status_code == 200:
                extension = content_type.split("/")[-1]
                filename = f"whatsapp_media/{timezone.now().strftime('%Y%m%d%H%M%S')}_{i}.{extension}"
                default_storage.save(filename, ContentFile(response.content))
                media_files.append(filename)

    return media_files


# @csrf_exempt
# def twilio_whatsapp_webhook(request):
#     from cogu.models import Commune, WhatsAppMessage, IncidentType, SanitaryIncident, IncidentMedia
#     if request.method != 'POST':
#         return HttpResponse("OK", status=200)
#
#     sender = request.POST.get('From', '').replace('whatsapp:', '')
#     message_body = request.POST.get('Body', '').strip()
#     num_media = int(request.POST.get('NumMedia', '0'))
#
#     WhatsAppMessage.objects.create(
#         direction='in',
#         sender=sender,
#         recipient=settings.TWILIO_WHATSAPP_NUMBER,
#         body=message_body
#     )
#
#     response = MessagingResponse()
#
#     try:
#         matched_commune = Commune.objects.filter(name__icontains=message_body).first()
#         location = matched_commune.location if matched_commune else get_location_from_text(message_body)
#         incident_type = IncidentType.objects.filter(name__iexact='Autre').first()
#
#         incident = SanitaryIncident.objects.create(
#             incident_type=incident_type,
#             description=message_body,
#             date_time=timezone.now(),
#             location=location,
#             city=matched_commune,
#             outcome='autre',
#             source='WhatsApp',
#             number_of_people_involved=1,
#         )
#
#         for i in range(num_media):
#             media_url = request.POST.get(f"MediaUrl{i}")
#             media_type = request.POST.get(f"MediaContentType{i}", "application/octet-stream")
#
#             media = IncidentMedia.objects.create(
#                 incident=incident,
#                 media_url=media_url,
#                 media_type=media_type
#             )
#
#             try:
#                 resp = requests.get(media_url, auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN))
#                 if resp.status_code == 200:
#                     ext = mimetypes.guess_extension(media_type) or ".bin"
#                     filename = f"incident_media/{timezone.now().strftime('%Y%m%d%H%M%S')}_{i}{ext}"
#                     media.downloaded_file.save(filename, ContentFile(resp.content))
#             except Exception as e:
#                 logger.warning(f"Erreur téléchargement média : {e}")
#
#         response.message(f"✅ Merci ! Incident enregistré (#INC-{incident.id:04d}).")
#
#         if "mort" in message_body.lower() or "urgence" in message_body.lower():
#             send_slack_alert(f"🚨 Incident critique via WhatsApp: {message_body}")
#             send_email_alert("Alerte Critique", message_body)
#
#         logger.info(f"[WhatsApp] Incident #{incident.id} enregistré avec {num_media} médias.")
#
#     except Exception as e:
#         logger.exception("Erreur webhook WhatsApp")
#         response.message("❌ Une erreur est survenue. Veuillez réessayer plus tard.")
#
#     return HttpResponse(str(response), content_type='application/xml')


def extract_info_from_message(message):
    keywords = {
        "épidémie": "Épidémie",
        "accident": "Accident",
        "blessé": "Blessure",
        "mort": "Décès"
    }
    incident_type = None
    gravité = "modérée"
    personnes = 1

    for mot, label in keywords.items():
        if mot in message.lower():
            incident_type = label
            if mot == "mort":
                gravité = "critique"

    possible_names = re.findall(r"[A-Z][a-z]+\s[A-Z][a-z]+", message)

    return {
        "incident_type_name": incident_type,
        "gravité": gravité,
        "patients": possible_names,
        "nombre": personnes,
    }

@csrf_exempt
def twilio_whatsapp_webhook(request):
    from cogu.models import Commune, WhatsAppMessage, IncidentType, SanitaryIncident, IncidentMedia,Patient

    if request.method != 'POST':
        return HttpResponse("OK", status=200)

    sender = request.POST.get('From', '').replace('whatsapp:', '')
    message_body = request.POST.get('Body', '').strip()
    num_media = int(request.POST.get('NumMedia', '0'))

    WhatsAppMessage.objects.create(
        direction='in', sender=sender,
        recipient=settings.TWILIO_WHATSAPP_NUMBER,
        body=message_body
    )

    response = MessagingResponse()

    try:
        info = extract_info_from_message(message_body)
        matched_commune = Commune.objects.filter(name__icontains=message_body).first()
        location = matched_commune.location if matched_commune else None

        incident_type = IncidentType.objects.filter(name__icontains=info['incident_type_name']).first()
        if not incident_type:
            incident_type = IncidentType.objects.filter(name__icontains='Autre').first()

        incident = SanitaryIncident.objects.create(
            incident_type=incident_type,
            description=message_body,
            date_time=timezone.now(),
            location=location,
            city=matched_commune,
            outcome='autre',
            source='WhatsApp',
            number_of_people_involved=info['nombre'],
            status='pending'
        )

        patients = Patient.objects.filter(full_name__in=info['patients'])
        incident.patients_related.set(patients)

        for i in range(num_media):
            media_url = request.POST.get(f"MediaUrl{i}")
            media_type = request.POST.get(f"MediaContentType{i}", "application/octet-stream")

            media = IncidentMedia.objects.create(
                incident=incident,
                media_url=media_url,
                media_type=media_type
            )

            try:
                resp = requests.get(media_url, auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN))
                if resp.status_code == 200:
                    ext = mimetypes.guess_extension(media_type) or ".bin"
                    filename = f"incident_media/{timezone.now().strftime('%Y%m%d%H%M%S')}_{i}{ext}"
                    media.downloaded_file.save(filename, ContentFile(resp.content))
            except Exception as e:
                logger.warning(f"Erreur téléchargement média : {e}")

        response.message(f"✅ Merci ! Incident enregistré (#INC-{incident.id:04d}).")

        if any(word in message_body.lower() for word in ["mort", "urgence", "épidémie", "panique", "hôpital"]):
            send_slack_alert(f"🚨 Incident critique via WhatsApp: {message_body}")
            send_email_alert("Alerte Critique", message_body)

        logger.info(f"[WhatsApp] Incident #{incident.id} enregistré. Média: {num_media}")

    except Exception as e:
        logger.exception("Erreur webhook WhatsApp")
        response.message("❌ Une erreur est survenue. Veuillez réessayer plus tard.")
        response.message(f"❌ Une erreur est survenue : {str(e)}")

    return HttpResponse(str(response), content_type='application/xml')


def get_location_from_text(text):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": text, "format": "json", "limit": 1}
        headers = {"User-Agent": "cogu-bot"}
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        if resp.status_code == 200 and resp.json():
            data = resp.json()[0]
            return Point(float(data['lon']), float(data['lat']))
    except Exception as e:
        logger.warning(f"Géolocalisation échouée: {e}")
    return None


def send_slack_alert(message: str, username="🛑 Alerte Incident"):
    webhook = getattr(settings, "SLACK_ALERT_WEBHOOK", None)
    if not webhook:
        logger.warning("SLACK_ALERT_WEBHOOK non configuré")
        return
    try:
        requests.post(webhook, json={"text": message, "username": username}, timeout=5)
        logger.info("Slack : message envoyé")
    except Exception as e:
        logger.error(f"Slack : erreur d'envoi - {e}")


def send_email_alert(subject: str, message: str):
    receivers = getattr(settings, "EMAIL_ALERT_RECEIVERS", [])
    if not receivers:
        logger.warning("EMAIL_ALERT_RECEIVERS non configuré")
        return
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, receivers, fail_silently=False)
        logger.info("Email : alerte envoyée")
    except Exception as e:
        logger.error(f"Email : erreur d'envoi - {e}")
