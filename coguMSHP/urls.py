"""
URL configuration for coguMSHP project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path

from cogu.api.views import DistrictListAPIView
from cogu.repport_send import send_generate_cogu_report, send_report_view
from cogu.views import (
    PatientListView, PatientCreateView, PatientDetailView, PatientUpdateView, PatientDeleteView,
    MajorEventListView, MajorEventCreateView, MajorEventDetailView, MajorEventUpdateView, MajorEventDeleteView,
    IncidentTypeListView, IncidentTypeCreateView, IncidentTypeDetailView, IncidentTypeUpdateView,
    IncidentTypeDeleteView,
    SanitaryIncidentListView, SanitaryIncidentCreateView, SanitaryIncidentDetailView,
    SanitaryIncidentUpdateView, SanitaryIncidentDeleteView, CADashborad, LandingView, IncidentToValidListView,
    WhatsAppMessageListView, validate_incident, reject_incident, IncidentMapView, PublicUserDashboard,
    PublicIncidentCreateView, PublicIncidentListView, PublicIncidentDetailView, PolitiqueConfidentialiteView,
    MajorEventGridView, contact, generate_cogu_report, IncidentReportView,
)
from coguMSHP.services import twilio_whatsapp_webhook, meta_whatsapp_webhook
from coguMSHP.utils import notifications
from coguMSHP.utils.notifications import send_whatsapp_message

urlpatterns = [
                  path("__reload__/", include("django_browser_reload.urls")),
                  path('backend/admin/v1', admin.site.urls),
                  path('api-auth/', include('rest_framework.urls')),
                  path('accounts/', include('allauth.urls')),

                  path('webhook/whatsapp/', twilio_whatsapp_webhook, name='twilio_whatsapp_webhook'),
                  # path('webhook/whatsapp/', meta_whatsapp_webhook, name='meta_whatsapp_webhook'),
                  path('notifications/', send_whatsapp_message, name='send_whatsapp_notify'),

                  path('dashboard', CADashborad.as_view(), name='home'),
                  path('contact/', contact, name='contact'),

                  path('patients/', PatientListView.as_view(), name='patient_list'),
                  path('patients/create/', PatientCreateView.as_view(), name='patient_create'),
                  path('patients/<str:code_patient>/', PatientDetailView.as_view(), name='patient_detail'),
                  path('patients/<str:code_patient>/update/', PatientUpdateView.as_view(), name='patient_update'),
                  path('patients/<str:code_patient>/delete/', PatientDeleteView.as_view(), name='patient_delete'),

                  # MajorEvent URLs
                  path('events/', MajorEventListView.as_view(), name='majorevent_list'),
                  path('events/grid', MajorEventGridView.as_view(), name='event_grid'),
                  path('events/create/', MajorEventCreateView.as_view(), name='majorevent_create'),
                  path('events/<int:pk>/', MajorEventDetailView.as_view(), name='majorevent_detail'),
                  path('events/<int:pk>/update/', MajorEventUpdateView.as_view(), name='majorevent_update'),
                  path('events/<int:pk>/delete/', MajorEventDeleteView.as_view(), name='majorevent_delete'),

                  # IncidentType URLs
                  path('incident-types/', IncidentTypeListView.as_view(), name='incidenttype_list'),
                  path('incident-types/create/', IncidentTypeCreateView.as_view(), name='incidenttype_create'),
                  path('incident-types/<int:pk>/', IncidentTypeDetailView.as_view(), name='incidenttype_detail'),
                  path('incident-types/<int:pk>/update/', IncidentTypeUpdateView.as_view(), name='incidenttype_update'),
                  path('incident-types/<int:pk>/delete/', IncidentTypeDeleteView.as_view(), name='incidenttype_delete'),

                  path('incidents/<int:pk>/valider/', validate_incident, name='incident_validate'),
                  path('incidents/<int:pk>/rejeter/', reject_incident, name='incident_reject'),
                  path('incidents/carte/', IncidentMapView.as_view(), name='incident_map'),
                  # SanitaryIncident URLs
                  path('whatsapp/', WhatsAppMessageListView.as_view(), name='whatsapp_list'),
                  path('incidents/', SanitaryIncidentListView.as_view(), name='sanitaryincident_list'),
                  path('incidents/traitment', IncidentToValidListView.as_view(),
                       name='sanitaryincident_non_valid_list'),
                  path('incidents/create/', SanitaryIncidentCreateView.as_view(), name='sanitaryincident_create'),
                  path('incidents/<int:pk>/', SanitaryIncidentDetailView.as_view(), name='sanitaryincident_detail'),
                  path('incidents/<int:pk>/update/', SanitaryIncidentUpdateView.as_view(),
                       name='sanitaryincident_update'),
                  path('incidents/<int:pk>/delete/', SanitaryIncidentDeleteView.as_view(),
                       name='sanitaryincident_delete'),

                  path('cogu-report/', generate_cogu_report, name='generate_cogu_report'),
                  path('cogu-report/', send_generate_cogu_report, name='send_generate_cogu_report'),
                  path('cogu-report/send/', send_report_view, name='send_generate_cogu_report'),
                  # path('cogu-report/pdf/', generate_cogu_report, {'format': 'pdf'}, name='generate_cogu_report_pdf'),
                  # path('cogu-report/word/', generate_cogu_report, {'format': 'word'}, name='generate_cogu_report_word'),

                  path('incidents/report/', IncidentReportView.as_view(), name='incident_report'),
                  # path('incidents/export/excel/', ExportIncidentsExcel.as_view(), name='export_incidents'),
                  # path('incidents/export/pdf/', ExportIncidentsPDF.as_view(), name='export_incidents_pdf'),
                  path('api/districts/', DistrictListAPIView.as_view(), name='district_list_api'),

                  #publique access

                  path('', LandingView.as_view(), name='landing'),
                  path('politique/de/confidentialite', PolitiqueConfidentialiteView.as_view(), name='politique'),
                  path('mon-espace/', PublicUserDashboard.as_view(), name='public_dashboard'),
                  path('mon-espace/Signaler/incident', PublicIncidentCreateView.as_view(),
                       name='public_incidentcreate'),
                  path('mon-espace/incident/list', PublicIncidentListView.as_view(), name='public_incidentlist'),

                  re_path(r'^mon-espace/incident/detail/incident-(?P<pk>\d+)/$', PublicIncidentDetailView.as_view(),
                          name='public_incidentdetail'),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
