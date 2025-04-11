import random

from django.core.management import BaseCommand

from rage.models import Commune, Patient


class Command(BaseCommand):
    help = "Met à jour la résidence_commune des patients qui n'en ont pas"

    def handle(self, *args, **options):
        communes = list(Commune.objects.all())  # Liste des communes disponibles

        if not communes:
            self.stdout.write(self.style.ERROR("🚨 Aucune commune trouvée ! Vérifiez que vous avez bien des communes en base."))
            return

        patients_a_mettre_a_jour = Patient.objects.filter(commune__isnull=True)

        if not patients_a_mettre_a_jour.exists():
            self.stdout.write(self.style.SUCCESS("✅ Tous les patients ont déjà une commune attribuée."))
            return

        self.stdout.write(f"🔄 Mise à jour de {patients_a_mettre_a_jour.count()} patients...")

        for patient in patients_a_mettre_a_jour:
            patient.commune = random.choice(communes)
            patient.save()

        self.stdout.write(self.style.SUCCESS(f"✅ {patients_a_mettre_a_jour.count()} patients mis à jour avec une résidence_commune !"))