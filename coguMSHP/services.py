import requests
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from coguMSHP.MPIClient import MPIClient


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

@csrf_exempt
def twilio_whatsapp_webhook(request):
    from cogu.models import IncidentType, SanitaryIncident, WhatsAppMessage

    if request.method == 'POST':
        # 📩 Numéro réel de l’expéditeur
        from_number = request.POST.get('From', '').replace('whatsapp:', '')
        message_body = request.POST.get('Body', '').strip()

        # ✅ Sauvegarder le message entrant
        WhatsAppMessage.objects.create(
            direction='in',
            sender=from_number,
            recipient=settings.TWILIO_WHATSAPP_NUMBER,
            body=message_body
        )

        try:
            incident_type = IncidentType.objects.get(name__iexact='Autre')

            incident = SanitaryIncident.objects.create(
                incident_type=incident_type,
                description=message_body,
                date_time=timezone.now(),
                outcome='autre',
                source='WhatsApp',
                number_of_people_involved=1,
            )

            response = MessagingResponse()
            response.message(f"✅ Merci ! Incident enregistré (#INC-{incident.id:04d}).")

        except Exception as e:
            print(f"[❌ Erreur WhatsApp webhook] {e}")
            response = MessagingResponse()
            response.message("❌ Une erreur est survenue. Veuillez réessayer plus tard.")

        return HttpResponse(str(response), content_type='application/xml')

    return HttpResponse("OK", status=200)