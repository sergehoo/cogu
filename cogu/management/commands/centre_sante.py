import pandas as pd
import requests
from django.core.management.base import BaseCommand

from cogu.models import ServiceSanitaire, TypeServiceSanitaire, DistrictSanitaire, HealthRegion, PolesRegionaux


class Command(BaseCommand):
    help = 'Importe les centres de santé depuis un fichier Excel et les géocode avec Mapbox'

    MAPBOX_ACCESS_TOKEN = 'pk.eyJ1Ijoib2dhaHNlcmdlIiwiYSI6ImNtMXc0dm91NjA0MW4ycXF5NzdtdThjeGYifQ.f1teke5Xjz5knfuLd0LpDA'  # Remplacez par votre jeton d'accès Mapbox

    def expand_acronyms(self, nom_centre):
        acronyms = {
            'EPH': 'Établissement Public Hospitalier',
            'EPHN': 'Établissements Publics Hospitalier Nationaux',
            'EPHR': 'Établissements Publics Hospitaliers Régionaux',
            'EPHD': 'Établissements Publics Hospitaliers Départementaux',
            'ESPC': 'Établissements de Santé de Premier Contact',
            'CHR': 'Centre de Santé Régional',
            'CHU': 'Centre de Santé Universitaire',
            'HG': 'Hopital Général',
            'CSR': 'Centre de Santé Régional',
            'CSU': 'Centre de Sante Urbain'
        }
        for acronym, full_name in acronyms.items():
            nom_centre = nom_centre.replace(acronym, full_name)
        return nom_centre

    def handle(self, *args, **kwargs):
        file_path = 'static/centre_sante.xlsx'  # Chemin vers le fichier Excel
        data = pd.read_excel(file_path, sheet_name='Feuil1')

        def geocode_location(nom_centre):
            try:
                url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{nom_centre}.json"
                params = {
                    'access_token': self.MAPBOX_ACCESS_TOKEN,
                    'country': 'CI',  # Côte d'Ivoire
                    'autocomplete': True,
                    'limit': 1
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                location = response.json()['features'][0]
                return (location['geometry']['coordinates'][1], location['geometry']['coordinates'][0])
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors du géocodage de {nom_centre}: {e}"))
                return None

        for index, row in data.iterrows():
            nom_centre = row['CENTRES DE SANTÉ']
            district_name = row['DISTRICT SANITAIRE']
            region_name = row['Region sanitaire']
            pole_name = row['Pole regional']
            type_centre = row['TYPE']

            # Expand acronyms in centre name
            nom_centre_expanded = self.expand_acronyms(nom_centre)

            # Get or create PoleRegionaux
            pole, _ = PolesRegionaux.objects.get_or_create(name=pole_name)

            # Get or create HealthRegion linked to PoleRegionaux
            region, _ = HealthRegion.objects.get_or_create(name=region_name, poles=pole)

            # Get or create DistrictSanitaire linked to HealthRegion
            district, _ = DistrictSanitaire.objects.get_or_create(nom=district_name, region=region)

            # Geocode the centre if coordinates are missing
            coords = geocode_location(nom_centre_expanded)
            if coords:
                latitude, longitude = coords
                geom_point = f"POINT({longitude} {latitude})"
            else:
                geom_point = None

            # Check if ServiceSanitaire already exists and update or create
            existing_service = ServiceSanitaire.objects.filter(nom=nom_centre, district=district).first()

            # Get or create TypeServiceSanitaire instance
            type_service, created = TypeServiceSanitaire.objects.get_or_create(acronyme=type_centre)

            # Update or set the name based on the acronym
            type_service.nom = self.expand_acronyms(type_centre)  # Utiliser la méthode pour compléter le nom
            type_service.save()  # Enregistrer les modifications

            if existing_service:
                # Update existing service
                existing_service.geom = geom_point
                existing_service.completeness = "partiel"
                existing_service.type = type_service
                existing_service.save()
                self.stdout.write(self.style.WARNING(f"Centre {nom_centre} mis à jour avec succès!"))
            else:
                # Create new ServiceSanitaire
                ServiceSanitaire.objects.create(
                    nom=nom_centre,
                    geom=geom_point,
                    district=district,
                    type=type_service,
                    completeness="partiel",
                    version=1
                )
                self.stdout.write(self.style.SUCCESS(f"Centre {nom_centre} ajouté avec succès!"))

