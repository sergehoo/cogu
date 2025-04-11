import time
import requests
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup
from django.contrib.gis.geos import Point
from tqdm import tqdm

from cogu.models import Commune, DistrictSanitaire


class Command(BaseCommand):
    help = "Importe les communes de Côte d'Ivoire avec coordonnées GPS et association automatique au district sanitaire."

    def handle(self, *args, **kwargs):
        url = "https://fr.wikipedia.org/wiki/Liste_des_communes_de_Côte_d'Ivoire"
        response = requests.get(url, timeout=15)

        if response.status_code != 200:
            self.stderr.write(self.style.ERROR(f"Erreur Wikipédia : {response.status_code}"))
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        raw_communes = [li.get_text(strip=True) for li in soup.select('div.mw-parser-output ul li')]
        communes = sorted(set(c for c in raw_communes if c and not Commune.objects.filter(name=c).exists()))

        self.stdout.write(self.style.NOTICE(f"{len(communes)} communes à importer."))

        results = []
        for commune in tqdm(communes, desc="Recherche OSM"):  # Modifier [:50] pour tout traiter
            geom = self.get_coordinates(commune)
            results.append(geom)
            time.sleep(1.2)  # Respect des limitations OSM

        communes_sans_coord = 0

        for name, geom in zip(communes, results):
            try:
                district = self.find_district(name)
                if not geom:
                    communes_sans_coord += 1

                Commune.objects.get_or_create(
                    name=name,
                    defaults={
                        'type': 'Commune',
                        'geom': geom,
                        'district': district
                    }
                )

                if district:
                    self.stdout.write(self.style.SUCCESS(f'✅ {name} liée à "{district.nom}"'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️  {name} sans district associé'))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Erreur commune {name}: {e}"))

        self.stdout.write(self.style.SUCCESS("🎉 Importation des communes terminée."))
        self.stdout.write(self.style.WARNING(f"⚠️  {communes_sans_coord} communes sans coordonnées."))

    def get_coordinates(self, commune_name):
        """Récupère les coordonnées GPS via OpenStreetMap"""
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={commune_name}, Côte d'Ivoire"
        headers = {
            "User-Agent": "DjangoApp/1.0 (contact@afriqconsulting.com)"  # Remplacer par ton vrai email
        }

        for _ in range(3):  # Jusqu'à 3 tentatives
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data:
                    return Point(float(data[0]['lon']), float(data[0]['lat']))
            except requests.exceptions.RequestException as e:
                self.stderr.write(self.style.WARNING(f"⏳ Erreur pour {commune_name}: {e}"))
                time.sleep(2)
        return None

    def find_district(self, commune_name):
        """Essaie d’associer une commune à un district sanitaire en comparant les noms"""
        commune_lower = commune_name.lower()

        for district in DistrictSanitaire.objects.all():
            if district.nom:
                nom_district = district.nom.lower()
                if commune_lower in nom_district or nom_district in commune_lower:
                    return district
        return None
