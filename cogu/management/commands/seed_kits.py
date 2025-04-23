import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from django.contrib.auth import get_user_model

from cogu.models import Fournisseur, KitCategorie, ComposantKit, ServiceSanitaire, StockCentre, Stock, Kit, \
    KitComposition, DeploiementKit, DistrictSanitaire

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = "Génère des données fictives pour les kits, composants, stock et déploiement"

    def add_arguments(self, parser):
        parser.add_argument('--kits', type=int, default=5)
        parser.add_argument('--composants', type=int, default=20)
        parser.add_argument('--centres', type=int, default=3)

    def handle(self, *args, **options):
        nb_kits = options['kits']
        nb_composants = options['composants']
        nb_centres = options['centres']

        user = User.objects.order_by('?').first()
        if not user:
            self.stdout.write(self.style.ERROR("Aucun utilisateur trouvé. Créez un utilisateur admin."))
            return

        # 1. Fournisseurs
        fournisseurs = [
            Fournisseur.objects.get_or_create(
                code_fournisseur=f"FR-{i}",
                defaults={
                    'nom': f"Fournisseur {i}",
                    'contact': fake.name(),
                    'telephone': fake.phone_number(),
                    'email': fake.email()
                }
            )[0] for i in range(1, 6)
        ]

        # 2. Catégories
        urgences = ['routine', 'urgence', 'critique']
        categories = [
            KitCategorie.objects.get_or_create(
                nom=f"Catégorie {i}",
                defaults={
                    'description': fake.text(),
                    'niveau_urgence': random.choice(urgences)
                }
            )[0] for i in range(1, 6)
        ]

        # 3. Composants
        composants = []
        unites = ['unite', 'boite', 'kg', 'litre']
        for i in range(nb_composants):
            composant = ComposantKit.objects.create(
                nom=f"Composant {i + 1}",
                code_produit=f"CP{i + 1}",
                unite_mesure=random.choice(unites),
                duree_conservation=random.randint(6, 36),
                temperature_stockage=random.choice(['Ambiance', 'Réfrigéré']),
                seuil_alerte=random.randint(5, 20)
            )
            composants.append(composant)

        # 4. Centres
        regions = list(ServiceSanitaire.objects.all())
        centres = []
        for i in range(nb_centres):
            centre = StockCentre.objects.create(
                nom=f"Centre {i + 1}",
                region=random.choice(regions),
                adresse=fake.address(),
                responsable=user,
                capacite_max=random.randint(1000, 5000),
                temperature_controlee=random.choice([True, False])
            )
            centres.append(centre)

        # 5. Stock
        for composant in composants:
            for centre in centres:
                Stock.objects.create(
                    centre=centre,
                    composant=composant,
                    quantite=random.randint(20, 100),
                    lot=f"LOT-{random.randint(1000, 9999)}",
                    date_expiration=timezone.now().date() + timedelta(days=random.randint(90, 720)),
                    fournisseur=random.choice(fournisseurs).nom,
                    created_by=user
                )

        # 6. Kits & Composition
        for i in range(nb_kits):
            kit = Kit.objects.create(
                reference=f"KIT-{1000 + i}",
                categorie=random.choice(categories),
                description=fake.text(),
                instructions=fake.text(max_nb_chars=200),
                capacite_personnes=random.randint(5, 100),
                created_by=user
            )
            composants_choisis = random.sample(composants, k=random.randint(3, 8))
            for c in composants_choisis:
                KitComposition.objects.create(
                    kit=kit,
                    composant=c,
                    quantite_standard=random.randint(1, 10)
                )

        # 7. Déploiements
        districts = list(DistrictSanitaire.objects.all())
        kits = list(Kit.objects.all())
        for i in range(5):
            DeploiementKit.objects.create(
                kit=random.choice(kits),
                quantite=random.randint(1, 5),
                centre_source=random.choice(centres),
                destination=random.choice(districts),
                date_envoi=timezone.now() - timedelta(days=random.randint(1, 30)),
                date_reception=timezone.now(),
                statut=random.choice(['recu', 'utilise']),
                responsable=user
            )

        self.stdout.write(
            self.style.SUCCESS(f"{nb_kits} kits, {nb_composants} composants, {nb_centres} centres créés avec succès !"))
