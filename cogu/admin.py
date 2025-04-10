from django.contrib import admin

from cogu.models import IncidentType, SanitaryIncident, MajorEvent, Patient, Commune, DistrictSanitaire, HealthRegion, \
    PolesRegionaux, EmployeeUser, WhatsAppMessage, IncidentMedia


# Register your models here.
# EmployeeUser
@admin.register(EmployeeUser)
class EmployeeUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'civilite', 'roleemployee', 'contact', 'email', 'fonction')
    list_filter = ('roleemployee', 'civilite')
    search_fields = ('username', 'email', 'fonction')


@admin.register(PolesRegionaux)
class PolesRegionauxAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(HealthRegion)
class HealthRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'poles')
    list_filter = ('poles',)
    search_fields = ('name',)


@admin.register(DistrictSanitaire)
class DistrictSanitaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region')
    list_filter = ('region',)
    search_fields = ('nom',)


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'population', 'district')
    list_filter = ('type', 'district')
    search_fields = ('name',)


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


@admin.register(SanitaryIncident)
class SanitaryIncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_type', 'date_time', 'city', 'number_of_people_involved', 'outcome', 'source')
    list_filter = ('incident_type', 'outcome')
    search_fields = ('description', 'source')
    filter_horizontal = ('patients_related',)


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'direction', 'sender', 'recipient', 'body')
    list_filter = ('direction', 'timestamp')
    search_fields = ('sender', 'recipient', 'body')


@admin.register(IncidentMedia)
class IncidentMediaAdmin(admin.ModelAdmin):
    list_display = ('incident', 'media_type', 'media_url', 'downloaded_file')
