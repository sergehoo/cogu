from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from leaflet.admin import LeafletGeoAdmin

from cogu.models import IncidentType, SanitaryIncident, MajorEvent, Patient, Commune, DistrictSanitaire, HealthRegion, \
    PolesRegionaux, EmployeeUser, WhatsAppMessage, IncidentMedia, ContactMessage, ReportRecipient, ServiceSanitaire, \
    TypeServiceSanitaire, MouvementStock, Stock, DeploiementKit, StockCentre, Kit, KitComposition, ComposantKit, \
    KitCategorie, Fournisseur


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    list_editable = ('is_read',)
    date_hierarchy = 'created_at'


# Register your models here.
# EmployeeUser
@admin.register(EmployeeUser)
class EmployeeUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'civilite', 'roleemployee', 'contact', 'email', 'fonction')
    list_filter = ('roleemployee', 'civilite')
    search_fields = ('username', 'email', 'fonction')


class PolesRegionauxResource(resources.ModelResource):
    class Meta:
        model = PolesRegionaux
        fields = ('id', 'name')


#
@admin.register(PolesRegionaux)
class PolesRegionauxAdmin(ImportExportModelAdmin):
    resource_class = PolesRegionauxResource
    list_display = ['name']
    search_fields = ['name']


class CommuneResource(resources.ModelResource):
    class Meta:
        model = Commune
        fields = ('id', 'name', 'type', 'population', 'is_in', 'district__nom', 'geom')


class DistrictSanitaireResource(resources.ModelResource):
    class Meta:
        model = DistrictSanitaire
        fields = ('id', 'nom', 'region', 'geom', 'geojson')


class HealthRegionResource(resources.ModelResource):
    class Meta:
        model = HealthRegion
        fields = ('id', 'name', 'poles')


@admin.register(HealthRegion)
class HealthRegionAdmin(ImportExportModelAdmin):
    resource_class = HealthRegionResource
    list_display = ('name', 'poles')
    search_fields = ('name',)
    list_filter = ('poles',)


# 🔹 Ajout du module ImportExportModelAdmin
@admin.register(Commune)
class CommuneAdmin(ImportExportModelAdmin, LeafletGeoAdmin):
    resource_class = CommuneResource
    list_display = ('name', 'district', 'population')
    search_fields = ('name', 'district__nom')
    list_filter = ('district',)
    ordering = ('name',)
    autocomplete_fields = ['district']

    # Personnalisation de Leaflet pour afficher les cartes correctement
    settings_overrides = {
        'DEFAULT_ZOOM': 7,
        'MIN_ZOOM': 5,
        'MAX_ZOOM': 28,
    }


@admin.register(DistrictSanitaire)
class DistrictSanitaireAdmin(ImportExportModelAdmin, LeafletGeoAdmin):
    resource_class = DistrictSanitaireResource
    list_display = ('nom', 'region')
    search_fields = ('nom', 'region__name')
    list_filter = ('region',)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenoms', 'code_patient', 'contact', 'date_naissance', 'status', 'gueris', 'decede')
    list_filter = ('status', 'gueris', 'decede', 'sexe', 'commune')
    search_fields = ('nom', 'prenoms', 'code_patient', 'contact', 'cni_num', 'cni_nni')


@admin.register(MajorEvent)
class MajorEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'organizer')
    search_fields = ('name', 'organizer')
    list_filter = ('start_date',)


@admin.register(IncidentType)
class IncidentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_type')
    list_filter = ('parent_type',)
    search_fields = ('name',)


# @admin.register(SanitaryIncident)
# class SanitaryIncidentAdmin(admin.ModelAdmin):
#     list_display = ('incident_type', 'date_time', 'city', 'number_of_people_involved', 'outcome', 'source')
#     list_filter = ('incident_type', 'outcome')
#     search_fields = ('description', 'source')
#     filter_horizontal = ('patients_related',)
@admin.register(SanitaryIncident)
class SanitaryIncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'incident_type', 'date_time', 'city', 'outcome', 'status', 'source')
    list_filter = ('status', 'incident_type', 'city', 'outcome')
    search_fields = ('description', 'city__name')
    actions = ['valider_incidents', 'rejeter_incidents']
    autocomplete_fields = ['city', 'centre_sante','incident_type']

    @admin.action(description="Valider les incidents sélectionnés")
    def valider_incidents(self, request, queryset):
        queryset.update(status='validated')

    @admin.action(description="Rejeter les incidents sélectionnés")
    def rejeter_incidents(self, request, queryset):
        queryset.update(status='rejected')


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'direction', 'sender', 'recipient', 'body')
    list_filter = ('direction', 'timestamp')
    search_fields = ('sender', 'recipient', 'body')


@admin.register(IncidentMedia)
class IncidentMediaAdmin(admin.ModelAdmin):
    list_display = ('incident', 'media_type', 'media_url', 'downloaded_file')


@admin.register(ReportRecipient)
class ReportRecipientAdmin(admin.ModelAdmin):
    list_display = ['email']


@admin.register(TypeServiceSanitaire)
class TypeServiceSanitaireAdmin(ImportExportModelAdmin):
    # resource_class = SyntheseDistrictResource
    list_display = ('nom', 'acronyme')
    search_fields = ['nom']
    list_filter = ['acronyme', 'nom']


@admin.register(ServiceSanitaire)
class ServiceSanitaireDistrictAdmin(ImportExportModelAdmin):
    # resource_class = SyntheseDistrictResource
    list_display = ('nom', 'commune')
    search_fields = ['nom', 'commune__name', 'type__acronyme']
    list_filter = ['type__acronyme', 'commune__name']


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_fournisseur', 'telephone', 'actif')
    search_fields = ('nom', 'code_fournisseur')
    list_filter = ('actif',)

@admin.register(KitCategorie)
class KitCategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau_urgence', 'created_at')
    search_fields = ('nom',)
    list_filter = ('niveau_urgence',)

@admin.register(ComposantKit)
class ComposantKitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'unite_mesure', 'seuil_alerte', 'duree_conservation', 'temperature_stockage')
    search_fields = ('nom', 'code_produit')
    list_filter = ('unite_mesure',)

class KitCompositionInline(admin.TabularInline):
    model = KitComposition
    extra = 1

@admin.register(Kit)
class KitAdmin(admin.ModelAdmin):
    list_display = ('reference', 'categorie', 'capacite_personnes', 'actif', 'created_at')
    search_fields = ('reference',)
    list_filter = ('categorie', 'actif')
    inlines = [KitCompositionInline]

@admin.register(StockCentre)
class StockCentreAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region', 'capacite_max', 'temperature_controlee', 'actif')
    search_fields = ('nom',)
    list_filter = ('region', 'actif')

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('composant', 'centre', 'quantite', 'lot', 'date_expiration', 'statut_stock')
    search_fields = ('composant__nom', 'lot')
    list_filter = ('centre', 'date_expiration')

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('composant', 'type_mouvement', 'quantite', 'centre_source', 'centre_destination', 'created_at')
    search_fields = ('composant__nom',)
    list_filter = ('type_mouvement', 'created_at')

@admin.register(DeploiementKit)
class DeploiementKitAdmin(admin.ModelAdmin):
    list_display = ('kit', 'quantite', 'centre_source', 'destination', 'statut', 'date_envoi', 'date_reception')
    search_fields = ('kit__reference', 'destination__nom')
    list_filter = ('statut', 'centre_source', 'destination')