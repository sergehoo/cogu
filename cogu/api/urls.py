from django.urls import path
from .views import (
    PatientListCreateView, PatientRetrieveUpdateDestroyView,
    MajorEventListCreateView, MajorEventRetrieveUpdateDestroyView,
    IncidentTypeListCreateView, IncidentTypeRetrieveUpdateDestroyView,
    SanitaryIncidentListCreateView, SanitaryIncidentRetrieveUpdateDestroyView,
)

urlpatterns = [
    # Patient URLs
    path('patients/', PatientListCreateView.as_view(), name='patient-list'),
    path('patients/<str:code_patient>/', PatientRetrieveUpdateDestroyView.as_view(), name='patient-detail'),

    # MajorEvent URLs
    path('events/', MajorEventListCreateView.as_view(), name='event-list'),
    path('events/<int:pk>/', MajorEventRetrieveUpdateDestroyView.as_view(), name='event-detail'),

    # IncidentType URLs
    path('incident-types/', IncidentTypeListCreateView.as_view(), name='incident-type-list'),
    path('incident-types/<int:pk>/', IncidentTypeRetrieveUpdateDestroyView.as_view(), name='incident-type-detail'),

    # SanitaryIncident URLs
    path('incidents/', SanitaryIncidentListCreateView.as_view(), name='incident-list'),
    path('incidents/<int:pk>/', SanitaryIncidentRetrieveUpdateDestroyView.as_view(), name='incident-detail'),
]