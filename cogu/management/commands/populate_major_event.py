from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from datetime import datetime
from cogu.models import MajorEvent
from django.contrib.gis.geos import Polygon

# Coordonnées englobant la Côte d'Ivoire (approximatives)
CIV_POLYGON = [
    (-8.6, 10.7),  # Nord-ouest
    (-2.4, 10.7),  # Nord-est
    (-2.4, 4.3),  # Sud-est
    (-8.6, 4.3),  # Sud-ouest
    (-8.6, 10.7)  # Fermeture
]

FESTIVALS = [
    # Événements nationaux
    {
        "name": "Fête Nationale de la Côte d'Ivoire",
        "description": "Célébration de l'indépendance du pays",
        "start_date": "2025-08-07 00:00:00",
        "end_date": "2025-08-07 23:59:59",
        "organizer": "Ministère de l'Intérieur",
        "recurring": True,
        "location_coords": []  # Vide, donc par défaut on utilisera CIV_POLYGON
    },
    {
        "name": "Fête du Travail",
        "description": "Célébration des travailleurs",
        "start_date": "2025-05-01 00:00:00",
        "end_date": "2025-05-01 23:59:59",
        "organizer": "Union des syndicats",
        "recurring": True,
        "location_coords": []
    },
    {
        "name": "Fête des Femmes",
        "description": "Journée nationale de la femme",
        "start_date": "2025-03-08 00:00:00",
        "end_date": "2025-03-08 23:59:59",
        "organizer": "Ministère de la Femme",
        "recurring": True,
        "location_coords": []
    },

    # Événements religieux
    {
        "name": "Noël",
        "description": "Fête chrétienne célébrant la naissance du Christ",
        "start_date": "2025-12-25 00:00:00",
        "end_date": "2025-12-25 23:59:59",
        "organizer": "Église de Côte d'Ivoire",
        "recurring": True,
        "location_coords": []
    },
    {
        "name": "Tabaski",
        "description": "Fête musulmane du sacrifice (Aid al-Adha)",
        "start_date": "2025-06-06 00:00:00",
        "end_date": "2025-06-06 23:59:59",
        "organizer": "Conseil Supérieur des Imams",
        "recurring": True,
        "location_coords": []
    },
    {
        "name": "Ramadan (Fin)",
        "description": "Fête musulmane marquant la fin du mois de jeûne",
        "start_date": "2025-03-31 00:00:00",
        "end_date": "2025-03-31 23:59:59",
        "organizer": "Conseil Supérieur des Imams",
        "recurring": True,
        "location_coords": []
    },
    {
        "name": "Pâques",
        "description": "Fête chrétienne de la résurrection du Christ",
        "start_date": "2025-04-20 00:00:00",
        "end_date": "2025-04-20 23:59:59",
        "organizer": "Église catholique et protestante",
        "recurring": True,
        "location_coords": []
    },
    {
        "name": "Ascension",
        "description": "Fête chrétienne célébrant l'ascension du Christ",
        "start_date": "2025-05-29 00:00:00",
        "end_date": "2025-05-29 23:59:59",
        "organizer": "Église catholique",
        "recurring": True,
        "location_coords": []
    },
    {
        "name": "Toussaint",
        "description": "Commémoration des saints",
        "start_date": "2025-11-01 00:00:00",
        "end_date": "2025-11-01 23:59:59",
        "organizer": "Église catholique",
        "recurring": True,
        "location_coords": []
    }
]


class Command(BaseCommand):
    help = "Crée automatiquement les événements majeurs annuels (nationaux et religieux)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Création des événements majeurs (nationaux et religieux)..."))

        for item in FESTIVALS:
            coords = item.get('location_coords', []) or CIV_POLYGON.copy()
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            poly = Polygon([coords])

            event, created = MajorEvent.objects.get_or_create(
                name=item['name'],
                defaults={
                    'description': item['description'],
                    'start_date': make_aware(datetime.strptime(item['start_date'], '%Y-%m-%d %H:%M:%S')),
                    'end_date': make_aware(datetime.strptime(item['end_date'], '%Y-%m-%d %H:%M:%S')),
                    'organizer': item['organizer'],
                    'location': poly
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✔️ {event.name} créé"))
            else:
                self.stdout.write(f"↪️ {event.name} existe déjà")

        self.stdout.write(self.style.SUCCESS("✅ Tous les événements majeurs ont été enregistrés."))
