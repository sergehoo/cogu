# cogu/context_processors.py
from .models import SanitaryIncident, WhatsAppMessage
from django.db.models import Count


def incident_status_counts(request):
    if not request.user.is_authenticated:
        return {}

    return {
        "incident_stats": {
            "validated": SanitaryIncident.objects.filter(status="validated").count(),
            "pending": SanitaryIncident.objects.filter(status="pending").count(),
            "rejected": SanitaryIncident.objects.filter(status="rejected").count(),
            "whatsapp": WhatsAppMessage.objects.all().count(),
        }
    }
