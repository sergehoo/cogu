from django.core.management.base import BaseCommand
from faker import Faker
import random
from django.contrib.gis.geos import Point
from datetime import timedelta
from django.utils import timezone

from cogu.models import (
    Patient, SanitaryIncident, IncidentType,
    Commune, MajorEvent
)

fake = Faker('fr_FR')


class Command(BaseCommand):
    help = "Génère des données fictives pour les patients et incidents sanitaires"

    def add_arguments(self, parser):
        parser.add_argument('--patients', type=int, default=50, help='Nombre de patients à générer')
        parser.add_argument('--incidents', type=int, default=30, help='Nombre d’incidents à générer')

    def handle(self, *args, **kwargs):
        nb_patients = kwargs['patients']
        nb_incidents = kwargs['incidents']

        self.stdout.write(self.style.SUCCESS(f"Génération de {nb_patients} patients et {nb_incidents} incidents..."))

        communes = list(Commune.objects.all())
        types = list(IncidentType.objects.all())

        if not types:
            types = [IncidentType.objects.create(name=fake.word()) for _ in range(5)]

        patients = []
        for _ in range(nb_patients):
            sexe = random.choice(['Homme', 'Femme'])
            patient = Patient.objects.create(
                nom=fake.last_name(),
                prenoms=fake.first_name_male() if sexe == 'Homme' else fake.first_name_female(),
                contact=fake.phone_number(),
                date_naissance=fake.date_of_birth(minimum_age=1, maximum_age=90),
                sexe=sexe,
                commune=random.choice(communes) if communes else None
            )
            patients.append(patient)

        for _ in range(nb_incidents):
            date_incident = timezone.now() - timedelta(days=random.randint(0, 60))
            incident = SanitaryIncident.objects.create(
                incident_type=random.choice(types),
                description=fake.sentence(),
                date_time=date_incident,
                location=Point(
                    random.uniform(-8.6, -2.5),  # longitude approximative en CI
                    random.uniform(4.0, 10.5)     # latitude approximative en CI
                ),
                city=random.choice(communes) if communes else None,
                number_of_people_involved=random.randint(1, 50),
                outcome=random.choice(['mort', 'blessure', 'sauvé', 'autre']),
                source=random.choice(['Radio', 'Témoin', 'Hôpital', 'Urgence']),
            )
            incident.patients_related.set(random.sample(patients, k=random.randint(1, min(5, len(patients)))))

        self.stdout.write(self.style.SUCCESS("✅ Données fictives générées avec succès."))