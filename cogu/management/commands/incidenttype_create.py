from django.core.management.base import BaseCommand
from cogu.models import IncidentType

CATEGORIES = {
    "Accidents et incidents divers": [
        "Accidents de la route",
        "Accidents ferroviaires",
        "Accidents aériens",
        "Accidents maritimes",
        "Accidents du travail",
        "Accidents industriels",
        "Accidents domestiques",
        "Incendies",
        "Explosions",
    ],
    "Urgences médicales": [
        "Crise cardiaque",
        "Accident vasculaire cérébral",
        "Arrêt cardiorespiratoire",
        "Overdose",
        "Intoxication",
        "Réactions allergiques graves",
        "Blessures sévères",
        "Brûlures graves",
        "Crises diabétiques",
    ],
    "Violences et abus": [
        "Violence domestique",
        "Violence sexuelle",
        "Violences basées sur le genre",
        "Violences conjugales",
        "Maltraitance d’enfants",
        "Maltraitance des personnes âgées",
        "Harcèlement et intimidation",
        "Trafic d’êtres humains",
    ],
    "Crises de santé mentale": [
        "Suicide",
        "Automutilation",
        "Crises psychotiques",
        "Dépression sévère",
        "Trouble de stress post-traumatique",
        "Attaques de panique",
    ],
    "Maladies infectieuses et épidémies": [
        "COVID-19",
        "Grippe saisonnière",
        "Fièvre jaune",
        "Ebola",
        "Mpox",
        "Méningite",
        "VIH/SIDA",
        "Choléra",
        "Paludisme",
        "Dengue",
        "Zika",
        "Tuberculose",
        "Rougeole",
        "Poliomyélite",
    ],
    "Catastrophes naturelles": [
        "Inondations",
        "Sécheresses",
        "Canicules",
        "Cyclones",
        "Tornades",
        "Tempêtes de neige",
        "Glissements de terrain",
        "Séismes",
        "Tsunamis",
        "Éruptions volcaniques",
        "Feux de forêt",
    ],
    "Catastrophes technologiques / industrielles": [
        "Fuites de produits chimiques",
        "Accidents nucléaires",
        "Pollutions industrielles",
        "Explosions dans les usines",
        "Effondrements de bâtiments",
    ],
    "Crises de sécurité publique": [
        "Actes terroristes",
        "Conflits armés",
        "Émeutes",
        "Kidnappings",
        "Tirs / fusillades",
    ],
    "Autres menaces et urgences": [
        "Noyade",
        "Famine",
        "Pannes d’électricité généralisées",
        "Ruptures d’approvisionnement en eau",
        "Crises de transport",
        "Catastrophes écologiques",
        "Intrusions et attaques cyber",
        "Épidémies de ravageurs",
        "Crises financières et économiques",
    ]
}


class Command(BaseCommand):
    help = "Crée automatiquement les types d'incidents à partir d'une liste catégorisée"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Création des types d'incidents..."))

        for category, types in CATEGORIES.items():
            parent, created = IncidentType.objects.get_or_create(name=category, parent_type=None)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✔️ Catégorie créée : {category}"))
            for name in types:
                child, created = IncidentType.objects.get_or_create(name=name, parent_type=parent)
                if created:
                    self.stdout.write(f"  - Type ajouté : {name}")

        self.stdout.write(self.style.SUCCESS("✅ Tous les types d'incidents ont été enregistrés."))
