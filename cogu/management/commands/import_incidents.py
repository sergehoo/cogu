import pandas as pd
import requests
from django.contrib.gis.gdal.geometries import Point
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from django.db import transaction
from datetime import datetime

from cogu.models import (
    SanitaryIncident, IncidentType, Commune, ServiceSanitaire
)

class Command(BaseCommand):
    help = "Importer des incidents sanitaires depuis un fichier Excel avec geocodage si besoin"

    MAPBOX_ACCESS_TOKEN = 'pk.eyJ1Ijoib2dhaHNlcmdlIiwiYSI6ImNtMXc0dm91NjA0MW4ycXF5NzdtdThjeGYifQ.f1teke5Xjz5knfuLd0LpDA'  # Remplacez par votre jeton d'accès Mapbox

    def add_arguments(self, parser):
        parser.add_argument("excel_path", type=str, help="Chemin vers le fichier Excel ")

    def safe_int(self, val):
        if pd.isna(val):
            return 0
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def geocode_location(self, nom):
        try:
            url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{nom}.json"
            params = {
                'access_token': self.MAPBOX_ACCESS_TOKEN,
                'country': 'CI',
                'limit': 1
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            features = response.json().get("features")
            if features:
                lon, lat = features[0]["geometry"]["coordinates"]
                return Point(lon, lat)
        except Exception as e:
            self.stderr.write(self.style.WARNING(f"[⚠] Géocodage échoué pour '{nom}' : {e}"))
        return None

    def handle(self, *args, **options):
        file_path = options["excel_path"]
        df = pd.read_excel(file_path)
        df.columns = [col.strip().lower() for col in df.columns]

        created_count = 0

        for index, row in df.iterrows():
            sid = transaction.savepoint()
            try:
                date = pd.to_datetime(row["date"])
                date_time = make_aware(datetime.combine(date, datetime.min.time()))

                type_name = str(row["type incident"]).strip()
                description = str(row.get("description", "")).strip()
                city_name = str(row["localite"]).strip()
                centre_nom = str(row["centre de sante"]).strip()

                n_victimes = self.safe_int(row.get("nombre de victimes"))
                n_deces = self.safe_int(row.get("nombre de dece"))
                n_blesses = self.safe_int(row.get("nombre de blesse"))

                incident_type, _ = IncidentType.objects.get_or_create(
                    name__iexact=type_name, defaults={"name": type_name}
                )
                commune = Commune.objects.filter(name__icontains=city_name).first()
                centre = ServiceSanitaire.objects.filter(nom__icontains=centre_nom).first()

                location = None
                if commune and commune.geom:
                    location = commune.geom
                elif commune:
                    location = self.geocode_location(commune.name)

                if not location and centre and centre.geom:
                    location = centre.geom
                elif not location and centre:
                    location = self.geocode_location(centre.nom)

                outcome = "mort" if n_deces > 0 else "blessure" if n_blesses > 0 else "autre"

                SanitaryIncident.objects.create(
                    incident_type=incident_type,
                    description=description,
                    date_time=date_time,
                    city=commune,
                    location=location,
                    centre_sante=centre,
                    number_of_people_involved=n_victimes,
                    deces_nbr=n_deces,
                    blessure_nbr=n_blesses,
                    outcome=outcome,
                    status="pending",
                    source="import_excel"
                )

                transaction.savepoint_commit(sid)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"[✓] Ligne {index+2} importée avec succès"))

            except Exception as e:
                transaction.savepoint_rollback(sid)
                self.stderr.write(self.style.ERROR(f"Erreur ligne {index + 2} : {e}"))

        self.stdout.write(self.style.SUCCESS(f"✅ {created_count} incidents importés avec succès."))

# class Command(BaseCommand):
#     help = "Importer des incidents sanitaires depuis un fichier Excel"
#
#     def add_arguments(self, parser):
#         parser.add_argument("excel_path", type=str, help="Chemin vers le fichier Excel à importer")
#
#     def safe_int(self, val):
#         if pd.isna(val):
#             return 0
#         try:
#             return int(val)
#         except (ValueError, TypeError):
#             return 0
#
#     def handle(self, *args, **options):
#         file_path = options["excel_path"]
#         df = pd.read_excel(file_path)
#         df.columns = [col.strip().lower() for col in df.columns]
#
#         created_count = 0
#
#         for index, row in df.iterrows():
#             sid = transaction.savepoint()
#             try:
#                 date = pd.to_datetime(row["date"])
#                 date_time = make_aware(datetime.combine(date, datetime.min.time()))
#
#                 type_name = str(row["type incident"]).strip()
#                 description = str(row.get("description", "")).strip()
#                 city_name = str(row["localite"]).strip()
#                 centre_nom = str(row["centre de sante"]).strip()
#
#                 n_victimes = self.safe_int(row.get("nombre de victimes"))
#                 n_deces = self.safe_int(row.get("nombre de dece"))
#                 n_blesses = self.safe_int(row.get("nombre de blesse"))
#
#                 # Liens externes
#                 incident_type, _ = IncidentType.objects.get_or_create(name__iexact=type_name,
#                                                                       defaults={"name": type_name})
#                 commune = Commune.objects.filter(name__icontains=city_name).first()
#                 centre = ServiceSanitaire.objects.filter(nom__icontains=centre_nom).first()
#                 location = commune.geom if commune and commune.geom else None
#
#                 outcome = "mort" if n_deces > 0 else "blessure" if n_blesses > 0 else "autre"
#
#                 SanitaryIncident.objects.create(
#                     incident_type=incident_type,
#                     description=description,
#                     date_time=date_time,
#                     city=commune,
#                     location=location,
#                     centre_sante=centre,
#                     number_of_people_involved=n_victimes,
#                     deces_nbr=n_deces,
#                     blessure_nbr=n_blesses,
#                     outcome=outcome,
#                     status="pending",
#                     source="import_excel"
#                 )
#
#                 transaction.savepoint_commit(sid)
#                 created_count += 1
#
#             except Exception as e:
#                 transaction.savepoint_rollback(sid)
#                 self.stderr.write(self.style.ERROR(f"Erreur ligne {index + 2} : {e}"))
#
#         self.stdout.write(self.style.SUCCESS(f"{created_count} incidents importés avec succès."))
