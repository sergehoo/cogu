import random
import string
import uuid
from datetime import date
from django.contrib.auth.models import AbstractUser

from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from djgeojson.fields import PointField
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _

from django.contrib.gis.db import models
from coguMSHP.services import synchroniser_avec_mpi
from coguMSHP.utils.phone import nettoyer_numero, formater_numero_local

# Create your models here.
situation_matrimoniales_choices = [
    ('Celibataire', 'Celibataire'),
    ('Concubinage', 'Concubinage'),
    ('Marie', 'Marié'),
    ('Divorce', 'Divorcé'),
    ('Veuf', 'Veuf'),
    ('Autre', 'Autre'),
]
Goupe_sanguin_choices = [
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
]
Patient_statut_choices = [
    ('Admis', 'Admis'),
    ('Sorti', 'Sorti'),
    ('Transféré', 'Transféré'),
    ('Décédé', 'Décédé'),
    ('Sous observation', 'Sous observation'),
    ('Sous traitement', 'Sous traitement'),
    ('Chirurgie programmée', 'Chirurgie programmée'),
    ('En chirurgie', 'En chirurgie'),
    ('Récupération post-opératoire', 'Récupération post-opératoire'),
    ('USI', 'Unité de soins intensifs (USI)'),
    ('Urgence', 'Urgence'),
    ('Consultation externe', 'Consultation externe'),
    ('Réhabilitation', 'Réhabilitation'),
    ('En attente de diagnostic', 'En attente de diagnostic'),
    ('Traitement en cours', 'Traitement en cours'),
    ('Suivi programmé', 'Suivi programmé'),
    ('Consultation', 'Consultation'),
    ('Sortie en attente', 'Sortie en attente'),
    ('Isolement', 'Isolement'),
    ('Ambulantoire', 'Ambulantoire'),
    ('Aucun', 'Aucun')
]
NIVEAU_ETUDE_CHOICES = [
    ('Non scolarisé', 'Non scolarisé'),
    ('Préscolaire', 'Préscolaire'),
    ('Primaire', 'Primaire'),
    ('Secondaire', 'Secondaire'),
    ('Supérieur', 'Supérieur'),
]
Sexe_choices = [('Masculin', 'Masculin'), ('Feminin', 'Féminin')]


class EmployeeUser(AbstractUser):
    ROLE_CHOICES = [
        ('National', 'National'),
        ('Regional', 'Régional'),
        ('DistrictSanitaire', 'District Sanitaire'),
        ('Centre', 'Centre de Sante'),
        ('Public', 'Utilisateur Publique'),
    ]
    CIVILITE_CHOICES = [
        ('Monsieur', 'Monsieur'),
        ('Madame', 'Madame'),
        ('Docteur', 'Docteur'),
        ('Professeur', 'Professeur'),
        ('Excellence', 'Excellence'),
        ('Honorable', 'Honorable'),
    ]
    civilite = models.CharField(max_length=10, choices=CIVILITE_CHOICES, blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    fonction = models.CharField(max_length=255, blank=True, null=True)
    photo = models.ImageField(upload_to='users/images/', default='users/images/user.webp', blank=True, null=True)
    roleemployee = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Public')

    # centre = models.ForeignKey('CentreAntirabique', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.username} - {self.roleemployee}"


# Modèle des Pôles Régionaux
class PolesRegionaux(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name if self.name else "Unnamed Pole"


# Modèle des Régions Sanitaires
class HealthRegion(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    poles = models.ForeignKey(PolesRegionaux, on_delete=models.SET_NULL, null=True, blank=True, related_name='regions')

    def __str__(self):
        return f"{self.name}-{self.poles}"


# Modèle des Districts Sanitaires
class DistrictSanitaire(models.Model):
    nom = models.CharField(max_length=100, unique=True, db_index=True, null=True, blank=True)
    region = models.ForeignKey(HealthRegion, on_delete=models.CASCADE, null=True, blank=True, related_name='districts')
    geom = PointField(null=True, blank=True)
    geojson = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f'{self.nom} -> {self.region}'


type_localite_choices = [
    ('Commune', 'Commune'),
    ('Village', 'Village'),
    ('Ville', 'Ville'),
    ('Quartier', 'Quartier'),
]


class Commune(models.Model):
    name = models.CharField(max_length=500, null=True, blank=True, unique=True, db_index=True)
    type = models.CharField(choices=type_localite_choices, max_length=100, null=True, blank=True)
    population = models.CharField(max_length=100, null=True, blank=True)
    is_in = models.CharField(max_length=255, null=True, blank=True)
    district = models.ForeignKey(DistrictSanitaire, on_delete=models.CASCADE, null=True, blank=True, )
    geom = models.PointField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.district}"


class ServiceSanitaire(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    district = models.ForeignKey(Commune, on_delete=models.CASCADE, null=True, blank=True, )
    geom = models.PointField(srid=4326, null=True, blank=True)
    upstream = models.CharField(max_length=255, null=True, blank=True)
    date_modified = models.DateTimeField(null=True, blank=True)
    source_url = models.URLField(max_length=500, null=True, blank=True)
    completeness = models.CharField(max_length=100, null=True, blank=True)
    uuid = models.UUIDField(null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    what3words = models.CharField(max_length=255, null=True, blank=True)
    version = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom}- {self.district} {self.geom}"


class Patient(models.Model):
    nature_acompagnateur_CHOICES = [
        ('Pere', 'Pere'),
        ('Mere', 'Mere'),
        ('Oncle', 'Oncle'),
        ('Tante', 'Tante'),
        ('Frère', 'Frère'),
        ('Soeure', 'Soeure'),
        ('Cousin', 'Cousin'),
        ('Cousine', 'Cousine'),
        ('Connaissance du quartier', 'Connaissance du quartier'),
        ('Voisin du quartier', 'Voisin du quartier'),
        ('Propriétaire animal ', 'Propriétaire animal ')
    ]
    code_patient = models.CharField(max_length=225, blank=True, unique=True, editable=False, db_index=True)
    mpi_upi = models.UUIDField(null=True, blank=True, unique=True, db_index=True)
    nom = models.CharField(max_length=225, db_index=True)
    prenoms = models.CharField(max_length=225, db_index=True)
    contact = models.CharField(max_length=20, db_index=True)
    date_naissance = models.DateField(db_index=True)
    sexe = models.CharField(max_length=10, choices=Sexe_choices, )
    num_cmu = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    cni_num = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    cni_nni = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    secteur_activite = models.CharField(max_length=200, null=True, blank=True)
    niveau_etude = models.CharField(choices=NIVEAU_ETUDE_CHOICES, max_length=500, null=True, blank=True)
    commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    quartier = models.CharField(max_length=255, blank=True, null=True)
    village = models.CharField(max_length=255, blank=True, null=True)
    # centre_ar = models.ForeignKey(CentreAntirabique, on_delete=models.SET_NULL, null=True, blank=True)
    # proprietaire_animal = models.BooleanField(default=False)
    # typeanimal = models.CharField(choices=typeAnimal_choices, max_length=255, blank=True, null=True)
    autretypeanimal = models.CharField(max_length=255, blank=True, null=True)
    patient_mineur = models.BooleanField(default=False)
    accompagnateur = models.CharField(max_length=255, blank=True, null=True)
    accompagnateur_contact = models.CharField(max_length=20, blank=True, null=True)
    accompagnateur_adresse = models.CharField(max_length=255, blank=True, null=True)
    accompagnateur_nature = models.CharField(choices=nature_acompagnateur_CHOICES, max_length=255, blank=True,
                                             null=True)
    accompagnateur_niveau_etude = models.CharField(choices=NIVEAU_ETUDE_CHOICES, max_length=255, blank=True, null=True)

    status = models.CharField(choices=Patient_statut_choices, max_length=100, default='Aucun', null=True, blank=True)
    gueris = models.BooleanField(default=False)
    decede = models.BooleanField(default=False)

    cause_deces = models.TextField(blank=True, null=True)
    date_deces = models.DateField(blank=True, null=True)

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, db_index=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']
        permissions = (('voir_patient', 'Peut voir patient'),)

    def save(self, *args, **kwargs):
        # Nettoyage des numéros avant sauvegarde
        self.contact = nettoyer_numero(self.contact)
        self.accompagnateur_contact = nettoyer_numero(self.accompagnateur_contact)

        # Générer un code_patient unique constitué de chiffres et de caractères alphabétiques
        if not self.code_patient:
            # Générer 16 chiffres à partir de l'UUID
            digits = ''.join(filter(str.isdigit, str(uuid.uuid4().int)))[:8]
            # Générer 4 caractères alphabétiques aléatoires
            letters = ''.join(random.choices(string.ascii_uppercase, k=4))
            # Combiner les chiffres et les lettres pour former le code_patient
            self.code_patient = digits + letters

        # 🔁 Synchronisation MPI
        if not self.mpi_upi:  # seulement si pas encore synchronisé
            try:
                self.mpi_upi = synchroniser_avec_mpi(self)
            except Exception as e:
                print(f"⚠️ Erreur MPI: {e}")

        super(Patient, self).save(*args, **kwargs)

    @property
    def contact_formatte(self):
        return formater_numero_local(self.contact)

    @property
    def accompagnateur_contact_formatte(self):
        return formater_numero_local(self.accompagnateur_contact)

    @property
    def calculate_age(self):
        if self.date_naissance:
            today = date.today()
            age = today.year - self.date_naissance.year - (
                    (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
            return age
        else:
            return None

    @property
    def latest_constante(self):
        return self.constantes.order_by('-created_at').first()

    def __str__(self):
        return f'{self.nom} {self.prenoms} -- {self.code_patient}'


class MajorEvent(models.Model):
    parent_event = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = gis_models.PolygonField(geography=True, null=True, blank=True, help_text="Zone couverte par l’événement")
    organizer = models.CharField(max_length=255, blank=True)
    recurring = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class IncidentType(models.Model):
    parent_type = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=100)  # Accident, Noyade, etc.

    def __str__(self):
        return self.name


class SanitaryIncident(models.Model):
    STATUS_CHOICES = [
        ('pending', 'À valider'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    incident_type = models.ForeignKey(IncidentType, on_delete=models.CASCADE, db_index=True)
    description = models.TextField()
    date_time = models.DateTimeField()
    location = gis_models.PointField(geography=True, null=True, blank=True, db_index=True)
    city = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    number_of_people_involved = models.PositiveIntegerField()
    outcome = models.CharField(max_length=100, choices=[
        ('mort', 'Décès'),
        ('blessure', 'Blessure'),
        ('sauvé', 'Sauvé'),
        ('autre', 'Autre'),
    ])
    source = models.CharField(max_length=255)
    event = models.ForeignKey(
        MajorEvent, null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text="Si l’incident est lié à un événement majeur"
        , db_index=True)
    message = models.ForeignKey(
        'WhatsAppMessage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents',
        help_text="Message WhatsApp à l’origine de l’incident, s’il y en a un"
        , db_index=True)
    patients_related = models.ManyToManyField(Patient, db_index=True)
    posted_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True, db_index=True,
                                  related_name='postedby')
    validated_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.incident_type.name} - {self.city} ({self.date_time.date()})"


class VictimCare(models.Model):
    incident = models.ForeignKey(SanitaryIncident, on_delete=models.CASCADE, related_name='victim_cares')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='cares')

    prise_en_charge_date = models.DateTimeField(default=timezone.now)
    type_prise_en_charge = models.CharField(max_length=255, choices=[
        ('soins', 'Soins médicaux'),
        ('hospitalisation', 'Hospitalisation'),
        ('vaccination', 'Vaccination'),
        ('psy', 'Soutien psychologique'),
        ('financier', 'Soutien Financier'),
        ('autre', 'Autre')
    ])
    description = models.TextField(blank=True)
    lieu_prise_en_charge = models.CharField(max_length=255, blank=True)
    servicedesante = models.ForeignKey(ServiceSanitaire, on_delete=models.SET_NULL, null=True, blank=True)
    intervenant = models.CharField(max_length=255, blank=True)
    est_prise_en_charge_effective = models.BooleanField(default=True)

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prise en charge de {self.patient} le {self.prise_en_charge_date.date()}"


class CareFollowUp(models.Model):
    care = models.ForeignKey(VictimCare, on_delete=models.CASCADE, related_name='followups')
    date = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=100, choices=[
        ('en cours', 'En cours'),
        ('terminé', 'Terminé'),
        ('référé', 'Référé'),
        ('non suivi', 'Non suivi')
    ])
    note = models.TextField(blank=True)
    professionnel = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Suivi {self.care.patient} - {self.statut} ({self.date.date()})"


# 4. Resource: Ressources disponibles pour les urgences
class Resource(models.Model):
    name = models.CharField(max_length=255, verbose_name=_("Nom de la ressource"))
    quantity = models.PositiveIntegerField(default=0, verbose_name=_("Quantité"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    location = models.ForeignKey(Commune, on_delete=models.CASCADE, verbose_name=_("Lieu"))

    def __str__(self):
        return f"{self.name} ({self.quantity})"

    class Meta:
        verbose_name = _("Ressource")
        verbose_name_plural = _("Ressources")


# 5. Respondent: Intervenants sur les incidents
class Respondent(models.Model):
    user = models.OneToOneField(EmployeeUser, on_delete=models.CASCADE, verbose_name=_("Utilisateur"))
    phone_number = models.CharField(max_length=15, verbose_name=_("Numéro de téléphone"))
    role = models.CharField(max_length=255, verbose_name=_("Rôle"))

    def __str__(self):
        return self.user.get_full_name()

    class Meta:
        verbose_name = _("Intervenant")
        verbose_name_plural = _("Intervenants")


# 6. IncidentReport: Rapports sur les incidents
class IncidentReport(models.Model):
    incident = models.ForeignKey(SanitaryIncident, on_delete=models.CASCADE, verbose_name=_("Incident sanitaire"))
    respondent = models.ForeignKey(Respondent, on_delete=models.SET_NULL, null=True, verbose_name=_("Intervenant"))
    report_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Date du rapport"))
    details = models.TextField(verbose_name=_("Détails"))

    def __str__(self):
        return f"Rapport {self.incident.title} par {self.respondent}"

    class Meta:
        verbose_name = _("Rapport d'incident")
        verbose_name_plural = _("Rapports d'incidents")


class WhatsAppMessage(models.Model):
    DIRECTION_CHOICES = (
        ('in', 'Reçu'),
        ('out', 'Envoyé'),
    )
    direction = models.CharField(max_length=3, db_index=True, choices=DIRECTION_CHOICES)
    sender = models.CharField(max_length=50)
    recipient = models.CharField(max_length=50)
    body = models.TextField(db_index=True)
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.get_direction_display()} | {self.sender} → {self.recipient}"


class IncidentMedia(models.Model):
    incident = models.ForeignKey("SanitaryIncident", on_delete=models.CASCADE, related_name="media", db_index=True)
    media_url = models.URLField(db_index=True)
    media_type = models.CharField(max_length=50, db_index=True)
    downloaded_file = models.FileField(upload_to='incident_media/', null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.media_type} - {self.media_url}"


class Testimony(models.Model):
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.created_by}"
