import json
import logging
import mimetypes
import os
import re
import uuid
from datetime import date

import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from coguMSHP.MPIClient import MPIClient
from coguMSHP.utils.notifications import send_email_alert
from dotenv import load_dotenv

load_dotenv()


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


def get_or_create_patient_from_full_name(full_name):
    from cogu.models import Patient
    parts = full_name.strip().split()
    if len(parts) < 2:
        return None
    nom = parts[0]
    prenoms = ' '.join(parts[1:])

    patient, created = Patient.objects.get_or_create(
        nom__iexact=nom,
        prenoms__iexact=prenoms,
        defaults={
            'nom': nom,
            'prenoms': prenoms,
            'contact': '0100000000',
            'date_naissance': date(2000, 1, 1),
            'sexe': 'M',
        }
    )
    return patient


def extract_info_from_message(message):
    keywords = {
        # Accidents et incidents divers
        "accident de la route": "Accidents de la route",
        "accident ferroviaire": "Accidents ferroviaires",
        "accident aérien": "Accidents aériens",
        "accident maritime": "Accidents maritimes",
        "accident du travail": "Accidents du travail",
        "accident industriel": "Accidents industriels",
        "accident domestique": "Accidents domestiques",
        "incendie": "Incendies",
        "explosion": "Explosions",

        # Urgences médicales
        "crise cardiaque": "Crise cardiaque",
        "infarctus": "Crise cardiaque",
        "avc": "Accident vasculaire cérébral",
        "arrêt cardiaque": "Arrêt cardiorespiratoire",
        "overdose": "Overdose",
        "intoxication": "Intoxication",
        "anaphylaxie": "Réactions allergiques graves",
        "blessé": "Blessures sévères",
        "traumatisme": "Blessures sévères",
        "brûlure": "Brûlures graves",
        "diabète": "Crises diabétiques",

        # Violences
        "violence domestique": "Violence domestique",
        "violence sexuelle": "Violence sexuelle",
        "violence conjugale": "Violences conjugales",
        "harcèlement": "Harcèlement et intimidation",
        "maltraitance": "Maltraitance d’enfants",

        # Santé mentale
        "suicide": "Suicide",
        "automutilation": "Automutilation",
        "psychose": "Crises psychotiques",
        "dépression": "Dépression sévère",
        "attaque de panique": "Attaques de panique",

        # Maladies épidémiques
        "covid": "COVID-19",
        "grippe": "Grippe saisonnière",
        "fièvre jaune": "Fièvre jaune",
        "ebola": "Ebola",
        "mpox": "Mpox",
        "méningite": "Méningite",
        "sida": "VIH/SIDA",
        "choléra": "Choléra",
        "paludisme": "Paludisme",
        "dengue": "Dengue",
        "zika": "Zika",
        "tuberculose": "Tuberculose",
        "rougeole": "Rougeole",
        "polio": "Poliomyélite",

        # Catastrophes naturelles
        "inondation": "Inondations",
        "sécheresse": "Sécheresses",
        "canicule": "Canicules",
        "cyclone": "Cyclones",
        "ouragan": "Cyclones",
        "tornade": "Tornades",
        "séisme": "Séismes",
        "tremblement de terre": "Séismes",
        "tsunami": "Tsunamis",
        "éruption": "Éruptions volcaniques",
        "feu de forêt": "Feux de forêt",

        # Sécurité publique
        "attentat": "Actes terroristes",
        "prise d'otage": "Actes terroristes",
        "fusillade": "Tirs / fusillades",
        "émeute": "Émeutes",
        "kidnapping": "Kidnappings",
        "conflit armé": "Conflits armés",
    }
    incident_type = None
    gravite = "modérée"
    personnes = 1

    for mot, label in keywords.items():
        if mot in message.lower():
            incident_type = label
            if mot == "mort":
                gravite = "critique"

    possible_names = re.findall(r"[A-Z][a-z]+\s[A-Z][a-z]+", message)

    return {
        "incident_type_name": incident_type,
        "gravité": gravite,
        "patients": possible_names,
        "nombre": personnes,
    }


@csrf_exempt
def twilio_whatsapp_webhook(request):
    from cogu.models import Commune, WhatsAppMessage, IncidentType, SanitaryIncident, IncidentMedia

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

        incident_type_name = info.get('incident_type_name')
        if incident_type_name:
            incident_type = IncidentType.objects.filter(name__icontains=incident_type_name).first()
        else:
            incident_type = None

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
            number_of_people_involved=info.get('nombre', 1),
            status='pending'
        )

        patients = []
        for full_name in info.get('patients', []):
            patient = get_or_create_patient_from_full_name(full_name)
            if patient:
                patients.append(patient)
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

    except Exception as e:
        logger.exception("Erreur webhook WhatsApp")
        response.message("❌ Une erreur est survenue. Veuillez réessayer plus tard.")
        response.message(f"❌ Détail : {str(e)}")

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


#-------------------------------
def get_media_url_from_meta(media_id):
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {
        "Authorization": f"Bearer {os.getenv('META_ACCESS_TOKEN')}"
    }
    resp = requests.get(url, headers=headers)
    return resp.json().get("url")


def download_and_attach_media(incident, media_url, content_type):
    from cogu.models import IncidentMedia

    try:
        response = requests.get(media_url, headers={
            "Authorization": f"Bearer {os.getenv('META_ACCESS_TOKEN')}"
        })
        if response.status_code == 200:
            ext = mimetypes.guess_extension(content_type) or ".bin"
            filename = f"incident_media/{timezone.now().strftime('%Y%m%d%H%M%S')}{ext}"
            media = IncidentMedia.objects.create(
                incident=incident,
                media_url=media_url,
                media_type=content_type
            )
            media.downloaded_file.save(filename, ContentFile(response.content))
    except Exception as e:
        logger.warning(f"Erreur téléchargement média WhatsApp Meta : {e}")


def send_whatsapp_message(to_number, message_text):
    import requests

    url = f"https://graph.facebook.com/v18.0/{os.getenv('META_PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('META_ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }

    response = requests.post(url, json=data, headers=headers)
    return response.status_code, response.json()


@csrf_exempt
def meta_whatsapp_webhook(request):
    from cogu.models import IncidentMedia, WhatsAppMessage, Commune, IncidentType, SanitaryIncident
    # Vérification du token pour l'enregistrement du webhook
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        print("GET PARAMS:", request.GET)

        print("🚨 TOKEN reçu par Meta:", token)
        print("✅ TOKEN attendu :", os.getenv("WHATSAPP_VERIFY_TOKEN"))

        if mode == "subscribe" and token == os.getenv('WHATSAPP_VERIFY_TOKEN'):
            return HttpResponse(challenge)
        return HttpResponseForbidden("Token invalide et non accessible")

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    contacts = value.get("contacts", [])

                    for msg in messages:
                        wa_id = msg["from"]
                        message_body = msg["text"]["body"] if msg["type"] == "text" else ""
                        timestamp = timezone.now()

                        # Enregistrement du message brut
                        wa_message = WhatsAppMessage.objects.create(
                            direction="in",
                            sender=wa_id,
                            recipient=os.getenv('META_PHONE_NUMBER_ID'),
                            body=message_body,
                            raw_payload=data
                        )

                        # Extraction d'infos à partir du texte
                        info = extract_info_from_message(message_body)
                        matched_commune = Commune.objects.filter(name__icontains=message_body).first()
                        location = matched_commune.location if matched_commune else None

                        incident_type_name = info.get("incident_type_name")
                        incident_type = IncidentType.objects.filter(name__icontains=incident_type_name).first() \
                            if incident_type_name else None
                        if not incident_type:
                            incident_type = IncidentType.objects.filter(name__icontains="Autre").first()

                        incident = SanitaryIncident.objects.create(
                            incident_type=incident_type,
                            description=message_body,
                            date_time=timestamp,
                            location=location,
                            city=matched_commune,
                            outcome='autre',
                            source='WhatsApp',
                            number_of_people_involved=info.get('nombre', 1),
                            status='pending',
                            message=wa_message
                        )

                        # Patients liés
                        patients = []
                        for full_name in info.get('patients', []):
                            patient = get_or_create_patient_from_full_name(full_name)
                            if patient:
                                patients.append(patient)
                        incident.patients_related.set(patients)

                        # Traitement médias (s’ils arrivent par messages séparés, il faut les gérer dans un autre webhook ou enrichissement ultérieur)
                        if msg.get("type") == "image":
                            media_id = msg["image"]["id"]
                            media_url = get_media_url_from_meta(media_id)
                            content_type = "image/jpeg"
                            download_and_attach_media(incident, media_url, content_type)
            send_whatsapp_message(wa_id, "✅ Merci pour votre signalement. Une équipe est informée.")
            return JsonResponse({"status": "received"})

        except Exception as e:
            logger.exception("Erreur webhook Meta WhatsApp")
            return JsonResponse({"error": str(e)}, status=500)
    return HttpResponse("Méthode non autorisée", status=405)
