import random
import string
import uuid
from datetime import date
from django.contrib.auth.models import AbstractUser, User

from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator
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

    centre = models.ForeignKey('ServiceSanitaire', on_delete=models.CASCADE, null=True, blank=True)

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


class TypeServiceSanitaire(models.Model):
    nom = models.CharField(max_length=500, null=True, blank=True)
    acronyme = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.acronyme}"


class ServiceSanitaire(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    type = models.ForeignKey(TypeServiceSanitaire, on_delete=models.SET_NULL, null=True, blank=True)
    commune = models.ForeignKey(Commune, on_delete=models.CASCADE, null=True, blank=True, )
    district = models.ForeignKey(DistrictSanitaire, on_delete=models.CASCADE, null=True, blank=True, )
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

    OUTCOME_CHOICES = [('mort', 'Décès'),
                       ('blessure', 'Blessure'),
                       ('sauvé', 'Sauvé'),
                       ('exeat', 'Exeat'),
                       ('evacue', 'Évacué'),
                       ('pris_charge', 'Pris en charge'),
                       ('autre', 'Autre'), ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    incident_type = models.ForeignKey(IncidentType, on_delete=models.CASCADE, db_index=True)
    description = models.TextField()
    date_time = models.DateTimeField()
    location = gis_models.PointField(geography=True, null=True, blank=True, db_index=True)
    city = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    centre_sante = models.ForeignKey(ServiceSanitaire, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    number_of_people_involved = models.PositiveIntegerField()
    outcome = models.CharField(max_length=100, choices=OUTCOME_CHOICES, db_index=True)
    deces_nbr = models.PositiveIntegerField()
    blessure_nbr = models.PositiveIntegerField()
    evacues_nbr = models.PositiveIntegerField(default=0)
    pris_en_charge_nbr = models.PositiveIntegerField(default=0)
    exeat_nbr = models.PositiveIntegerField(default=0)
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

    @property
    def severity(self):
        """
        Retourne un niveau de sévérité basé sur le nombre de personnes ou le résultat.
        Adapte cette logique selon ton besoin métier.
        """
        if self.number_of_people_involved >= 5 or self.outcome == 'mort':
            return 'high'
        elif self.number_of_people_involved >= 2:
            return 'medium'
        else:
            return 'low'

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


class ReportRecipient(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email


class Testimony(models.Model):
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.created_by}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(verbose_name="Email")
    subject = models.CharField(max_length=200, verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    is_read = models.BooleanField(default=False, verbose_name="Lu")

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ['-created_at']

    def __str__(self):
        return f"Message de {self.name} - {self.subject}"


#--------Gestion des kits

class Fournisseur(models.Model):
    """Modèle pour les fournisseurs comme NPSP"""
    nom = models.CharField(max_length=100, unique=True)
    code_fournisseur = models.CharField(max_length=50, unique=True)
    contact = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.code_fournisseur})"


class KitCategorie(models.Model):
    """Catégorie de kits (ex: Premiers soins, Choléra, COVID-19)"""
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    niveau_urgence = models.CharField(
        max_length=20,
        choices=[('routine', 'Routine'), ('urgence', 'Urgence'), ('critique', 'Critique')],
        default='urgence'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Catégorie de kit"
        verbose_name_plural = "Catégories de kits"
        ordering = ['niveau_urgence', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.get_niveau_urgence_display()})"


class ComposantKit(models.Model):
    """Composants individuels des kits"""
    nom = models.CharField(max_length=100)
    kit_type = models.ForeignKey(KitCategorie, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    code_produit = models.CharField(max_length=50, unique=True, blank=True, null=True)
    unite_mesure = models.CharField(max_length=20, choices=[
        ('unite', 'Unité'),
        ('boite', 'Boîte'),
        ('carton', 'Carton'),
        ('kg', 'Kilogramme'),
        ('litre', 'Litre')
    ])
    duree_conservation = models.PositiveIntegerField(
        help_text="Durée en mois avant péremption",
        validators=[MinValueValidator(1)]
    )
    temperature_stockage = models.CharField(
        max_length=50,
        help_text="Conditions de stockage recommandées",
        default="Ambiance"
    )
    seuil_alerte = models.PositiveIntegerField(
        default=10,
        help_text="Seuil minimum pour déclencher une alerte"
    )

    class Meta:
        verbose_name = "Composant de kit"
        verbose_name_plural = "Composants de kits"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.unite_mesure})"


class Kit(models.Model):
    """Modèle principal pour les kits d'urgence"""
    reference = models.CharField(max_length=50, unique=True)
    categorie = models.ForeignKey(KitCategorie, on_delete=models.PROTECT)
    composants = models.ManyToManyField(
        ComposantKit,
        through='KitComposition',
        through_fields=('kit', 'composant'),
        related_name='kits'
    )
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True, help_text="Instructions d'utilisation")
    capacite_personnes = models.PositiveIntegerField(
        default=1,
        help_text="Nombre de personnes que le kit peut couvrir"
    )
    actif = models.BooleanField(default=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True, related_name='kits_crees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kit d'urgence"
        verbose_name_plural = "Kits d'urgence"
        ordering = ['categorie', 'reference']

    def __str__(self):
        return f"{self.reference} - {self.categorie.nom}"

    @property
    def statut_stock(self):
        """Calcule le statut global du stock basé sur les composants"""
        compositions = self.compositions.all()
        if not compositions.exists():
            return 'inconnu'

        statuts = [comp.statut_stock for comp in compositions]
        if any(s == 'critique' for s in statuts):
            return 'critique'
        elif any(s == 'alerte' for s in statuts):
            return 'alerte'
        return 'suffisant'


class KitComposition(models.Model):
    """Table de liaison entre Kit et Composant avec quantités"""
    kit = models.ForeignKey(Kit, on_delete=models.CASCADE, related_name='compositions')
    composant = models.ForeignKey(ComposantKit, on_delete=models.CASCADE)
    quantite_standard = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        unique_together = ('kit', 'composant')
        verbose_name = "Composition de kit"
        verbose_name_plural = "Compositions de kits"

    def __str__(self):
        return f"{self.kit.reference} - {self.composant.nom} x{self.quantite_standard}"


class StockCentre(models.Model):
    """Centre de stockage des kits"""
    nom = models.CharField(max_length=100)
    region = models.ForeignKey('ServiceSanitaire', on_delete=models.PROTECT)
    adresse = models.TextField()
    responsable = models.ForeignKey(EmployeeUser, on_delete=models.PROTECT, related_name='centres_responsables')
    capacite_max = models.PositiveIntegerField(help_text="Capacité totale en unités de stockage")
    temperature_controlee = models.BooleanField(default=False)
    actif = models.BooleanField(default=True)
    date_creation = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Centre de stockage"
        verbose_name_plural = "Centres de stockage"
        ordering = ['region', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.region.nom})"

    @property
    def taux_remplissage(self):
        """Calcule le pourcentage d'occupation du stock"""
        total = self.stocks.aggregate(total=models.Sum('quantite'))['total'] or 0
        return round((total / self.capacite_max) * 100, 2)


class Stock(models.Model):
    """Stock physique des composants dans les centres"""
    centre = models.ForeignKey(StockCentre, on_delete=models.CASCADE, related_name='stocks')
    composant = models.ForeignKey(ComposantKit, on_delete=models.CASCADE, related_name='stocks')
    quantite = models.PositiveIntegerField(default=0)
    lot = models.CharField(max_length=50, blank=True)
    date_expiration = models.DateField()
    date_reception = models.DateField(default=timezone.now)
    fournisseur = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        ordering = ['composant', 'date_expiration']
        unique_together = ('centre', 'composant', 'lot')

    def __str__(self):
        return f"{self.composant.nom} x{self.quantite} ({self.centre.nom})"

    @property
    def statut_stock(self):
        """Détermine le statut du stock"""
        if self.quantite <= 0:
            return 'epuise'
        elif self.quantite <= self.composant.seuil_alerte:
            return 'critique'
        elif self.quantite <= (self.composant.seuil_alerte * 2):
            return 'alerte'
        return 'suffisant'

    @property
    def jours_avant_expiration(self):
        """Calcule le nombre de jours avant expiration"""
        delta = self.date_expiration - timezone.now().date()
        return delta.days


class MouvementStock(models.Model):
    """Trace toutes les transactions de stock"""
    TYPE_MOUVEMENT = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
        ('transfert', 'Transfert'),
        ('ajustement', 'Ajustement'),
        ('perte', 'Perte')
    ]

    composant = models.ForeignKey(ComposantKit, on_delete=models.PROTECT, related_name='mouvements')
    quantite = models.PositiveIntegerField()
    type_mouvement = models.CharField(max_length=20, choices=TYPE_MOUVEMENT)
    centre_source = models.ForeignKey(
        StockCentre,
        on_delete=models.PROTECT,
        related_name='sorties',
        null=True,
        blank=True
    )
    centre_destination = models.ForeignKey(
        StockCentre,
        on_delete=models.PROTECT,
        related_name='entrees',
        null=True,
        blank=True
    )
    kit = models.ForeignKey(
        Kit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Si lié à un kit spécifique"
    )
    incident = models.ForeignKey(
        'SanitaryIncident',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Si lié à un incident sanitaire"
    )
    created_by = models.ForeignKey(EmployeeUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_mouvement_display()} {self.composant.nom} x{self.quantite}"

    def save(self, *args, **kwargs):
        """Met à jour automatiquement les stocks après un mouvement"""
        super().save(*args, **kwargs)
        self.update_stock()

    def update_stock(self):
        """Met à jour les stocks selon le type de mouvement"""
        if self.type_mouvement == 'entree':
            stock, created = Stock.objects.get_or_create(
                centre=self.centre_destination,
                composant=self.composant,
                defaults={
                    'quantite': self.quantite,
                    'date_expiration': timezone.now() + timezone.timedelta(days=365)
                }
            )
            if not created:
                stock.quantite += self.quantite
                stock.save()
        elif self.type_mouvement == 'sortie':
            stock = Stock.objects.get(centre=self.centre_source, composant=self.composant)
            stock.quantite -= self.quantite
            stock.save()


class DeploiementKit(models.Model):
    """Enregistre les déploiements de kits sur le terrain"""
    STATUT_DEPLOIEMENT = [
        ('preparation', 'En préparation'),
        ('envoye', 'Envoyé'),
        ('recu', 'Reçu'),
        ('utilise', 'Utilisé'),
        ('retourne', 'Retourné'),
        ('perdu', 'Perdu')
    ]

    kit = models.ForeignKey(Kit, on_delete=models.PROTECT, related_name='deploiements')
    quantite = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    centre_source = models.ForeignKey(StockCentre, on_delete=models.PROTECT, related_name='envois')
    destination = models.ForeignKey('DistrictSanitaire', on_delete=models.PROTECT)
    date_envoi = models.DateTimeField()
    date_reception = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_DEPLOIEMENT, default='preparation')
    incident = models.ForeignKey(
        'SanitaryIncident',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kits_deployes'
    )
    responsable = models.ForeignKey(EmployeeUser, on_delete=models.PROTECT, related_name='deploiements')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Déploiement de kit"
        verbose_name_plural = "Déploiements de kits"
        ordering = ['-date_envoi']

    def __str__(self):
        return f"{self.kit.reference} x{self.quantite} vers {self.destination.nom}"

    @property
    def delai_livraison(self):
        """Calcule le délai de livraison si reçu"""
        if self.date_reception:
            return (self.date_reception - self.date_envoi).total_seconds() / 3600  # en heures
        return None


class CoguReport(models.Model):
    REPORT_FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('word', 'Word'),
    ]

    created_by = models.ForeignKey(EmployeeUser, on_delete=models.SET_NULL, null=True)
    report_date = models.DateField(verbose_name="Date du rapport")
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    comments = models.TextField(verbose_name="Commentaires", blank=True, null=True)
    format = models.CharField(max_length=10, choices=REPORT_FORMAT_CHOICES)
    file = models.FileField(upload_to='reports/cogu/', null=True, blank=True)
    sent_by_email = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rapport COGU du {self.report_date.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Rapport COGU"
        verbose_name_plural = "Rapports COGU"
