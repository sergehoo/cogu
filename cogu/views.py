from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.html import format_html
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView

from cogu.filters import PatientFilter
from cogu.forms import SanitaryIncidentForm
from cogu.models import Patient, MajorEvent, IncidentType, SanitaryIncident, Commune
from django.contrib.gis.geos import Point

# Create your views here.

class Landing(TemplateView):
    template_name = "pages/landing.html"
    # login_url = '/accounts/login/'


class CADashborad(TemplateView):
    template_name = "pages/dashboard.html"

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        last_month = now - timedelta(days=30)

        incidents_qs = SanitaryIncident.objects.all()
        incidents_count = incidents_qs.count()

        active_cases_qs = incidents_qs.filter(Q(outcome='mort') | Q(outcome='blessure'))
        active_cases_count = active_cases_qs.count()

        interventions_qs = incidents_qs.filter(patients_related__isnull=False).distinct()
        interventions_count = interventions_qs.count()

        resolved_cases_qs = incidents_qs.filter(outcome='sauvé')
        resolved_cases_count = resolved_cases_qs.count()

        # Variation mensuelle
        incidents_last_month = incidents_qs.filter(date_time__gte=last_month).count()
        incidents_monthly_change = self.calculate_change(incidents_last_month, incidents_count)

        active_cases_last_month = active_cases_qs.filter(date_time__gte=last_month).count()
        interventions_last_month = interventions_qs.filter(date_time__gte=last_month).count()
        resolved_last_month = resolved_cases_qs.filter(date_time__gte=last_month).count()

        # Pourcentages basés sur des bases réalistes
        incidents_percentage = (incidents_last_month / max(1, incidents_count)) * 100
        active_cases_percentage = (active_cases_count / max(1, incidents_count)) * 100
        interventions_percentage = (interventions_count / max(1, incidents_count)) * 100
        resolved_percentage = (resolved_cases_count / max(1, incidents_count)) * 100

        # Incidents critiques pour alertes
        incidents_critical = incidents_qs.filter(outcome='mort').order_by('-date_time')[:1]

        # Derniers incidents paginés
        recent_incidents = SanitaryIncident.objects.select_related('incident_type', 'city').order_by('-date_time')
        paginator = Paginator(recent_incidents, 10)
        page = request.GET.get("page")
        recent_incidents_page = paginator.get_page(page)

        # Données pour les graphiques
        regions_data = self.get_regions_data()
        monthly_data = self.get_monthly_trends()
        incident_types_data = self.get_incident_types_data()

        # Données carte
        incidents_map_data = list(SanitaryIncident.objects.filter(
            location__isnull=False
        ).values(
            'id', 'incident_type__name', 'incident_type_id', 'city__name', 'date_time', 'location'
        ))

        context = {
            'incidents_count': incidents_count,
            'active_cases': active_cases_count,
            'interventions_count': interventions_count,
            'resolved_cases': resolved_cases_count,
            'incidents_percentage': round(incidents_percentage, 1),
            'incidents_monthly_change': incidents_monthly_change,
            'active_cases_percentage': round(active_cases_percentage, 1),
            'active_cases_change': self.calculate_change(active_cases_last_month, active_cases_count),
            'interventions_percentage': round(interventions_percentage, 1),
            'interventions_change': self.calculate_change(interventions_last_month, interventions_count),
            'resolved_percentage': round(resolved_percentage, 1),
            'resolved_change': self.calculate_change(resolved_last_month, resolved_cases_count),
            'incidents_critical': incidents_critical,
            'recent_incidents': recent_incidents_page,
            'incident_types': IncidentType.objects.all(),
            'regions_labels': [r['name'] for r in regions_data],
            'regions_data': [r['count'] for r in regions_data],
            'monthly_labels': [m['month'] for m in monthly_data],
            'monthly_data': [m['count'] for m in monthly_data],
            'incident_types_labels': [t['name'] for t in incident_types_data],
            'incident_types_data': [t['count'] for t in incident_types_data],
            'incidents_map_data': incidents_map_data,
        }

        return self.render_to_response(context)

    def calculate_change(self, last, current):
        if last == 0:
            return current * 100 if current else 0
        return round(((current - last) / last) * 100, 1)

    def get_regions_data(self):
        return (
            SanitaryIncident.objects
            .filter(city__district__region__isnull=False)
            .values(name=F('city__district__region__name'))
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    def get_monthly_trends(self):
        return (
            SanitaryIncident.objects
            .annotate(month=F('date_time__month'))
            .values(month=F('month'))
            .annotate(count=Count('id'))
            .order_by('month')
        )
    def get_incident_types_data(self):
        return (
            SanitaryIncident.objects
            .values(name=F('incident_type__name'))
            .annotate(count=Count('id'))
            .order_by('-count')
        )


class PatientListView(ListView):
    model = Patient
    template_name = 'patient/list.html'
    context_object_name = 'patients'
    paginate_by = 20
    ordering = ['-created_at']
    filterset_class = PatientFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')

        if search_query:
            queryset = queryset.filter(
                Q(nom__icontains=search_query) |
                Q(prenoms__icontains=search_query) |
                Q(code_patient__icontains=search_query) |
                Q(contact__icontains=search_query)
            )

        return queryset


class PatientCreateView(CreateView):
    model = Patient
    template_name = 'patient/create.html'
    fields = '__all__'
    success_url = reverse_lazy('patient_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f"Patient {self.object} créé avec succès!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Nouveau Patient"
        return context


class PatientDetailView(DetailView):
    model = Patient
    template_name = 'patient/detail.html'
    context_object_name = 'patient'
    slug_field = 'code_patient'
    slug_url_kwarg = 'code_patient'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Détails Patient - {self.object.code_patient}"
        return context


class PatientUpdateView(UpdateView):
    model = Patient
    template_name = 'patient/update.html'
    fields = '__all__'
    slug_field = 'code_patient'
    slug_url_kwarg = 'code_patient'
    success_url = reverse_lazy('patient_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Patient {self.object} mis à jour avec succès!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Modifier Patient - {self.object.code_patient}"
        return context


class PatientDeleteView(DeleteView):
    model = Patient
    template_name = 'patient/delete.html'
    slug_field = 'code_patient'
    slug_url_kwarg = 'code_patient'
    success_url = reverse_lazy('patient_list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Patient {self.object} supprimé avec succès!")
        return response


class MajorEventListView(ListView):
    model = MajorEvent
    template_name = 'majorevent/list.html'
    context_object_name = 'events'
    paginate_by = 20
    ordering = ['-start_date']


class MajorEventCreateView(CreateView):
    model = MajorEvent
    template_name = 'majorevent/event_create.html'
    fields = '__all__'
    success_url = reverse_lazy('majorevent_list')


class MajorEventDetailView(DetailView):
    model = MajorEvent
    template_name = 'majorevent/event_detail.html'
    context_object_name = 'event'


class MajorEventUpdateView(UpdateView):
    model = MajorEvent
    template_name = 'majorevent/event_update.html'
    fields = '__all__'
    success_url = reverse_lazy('majorevent_list')


class MajorEventDeleteView(DeleteView):
    model = MajorEvent
    template_name = 'majorevent/event_delete.html'
    success_url = reverse_lazy('majorevent_list')


class IncidentTypeListView(ListView):
    model = IncidentType
    template_name = 'incidenttype/incidentlist.html'
    context_object_name = 'types'
    ordering = ['name']


class IncidentTypeCreateView(CreateView):
    model = IncidentType
    template_name = 'incidenttype/incidentcreate.html'
    fields = '__all__'
    success_url = reverse_lazy('incidenttype_list')


class IncidentTypeDetailView(DetailView):
    model = IncidentType
    template_name = 'incidenttype/incidentdetail.html'
    context_object_name = 'type'


class IncidentTypeUpdateView(UpdateView):
    model = IncidentType
    template_name = 'incidenttype/incidentupdate.html'
    fields = '__all__'
    success_url = reverse_lazy('incidenttype_list')


class IncidentTypeDeleteView(DeleteView):
    model = IncidentType
    template_name = 'incidenttype/incidentdelete.html'
    success_url = reverse_lazy('incidenttype_list')


class SanitaryIncidentListView(ListView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/list.html'
    context_object_name = 'incidents'
    paginate_by = 20
    ordering = ['-date_time']


class SanitaryIncidentCreateView(CreateView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/create.html'
    form_class = SanitaryIncidentForm
    success_url = reverse_lazy('sanitaryincident_list')

    def form_valid(self, form):
        messages.success(self.request, 'Incident enregistré avec succès!')
        return super().form_valid(form)


    def form_invalid(self, form):
        messages.error(self.request, 'Veuillez corriger les erreurs ci-dessous :')

        # Boucle sur les champs pour afficher chaque erreur individuellement
        for field, errors in form.errors.items():
            field_label = form.fields.get(field).label if field in form.fields else field
            for error in errors:
                messages.error(self.request, format_html("<strong>{}</strong>: {}", field_label, error))

        return super().form_invalid(form)


class SanitaryIncidentDetailView(DetailView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/detail.html'
    context_object_name = 'incident'


class SanitaryIncidentUpdateView(UpdateView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/update.html'
    form_class = SanitaryIncidentForm
    success_url = reverse_lazy('sanitaryincident_list')

    def form_valid(self, form):
        messages.success(self.request, 'Incident enregistré avec succès!')
        return super().form_valid(form)


    def form_invalid(self, form):
        messages.error(self.request, 'Veuillez corriger les erreurs ci-dessous :')

        # Boucle sur les champs pour afficher chaque erreur individuellement
        for field, errors in form.errors.items():
            field_label = form.fields.get(field).label if field in form.fields else field
            for error in errors:
                messages.error(self.request, format_html("<strong>{}</strong>: {}", field_label, error))

        return super().form_invalid(form)


class SanitaryIncidentDeleteView(DeleteView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/delete.html'
    success_url = reverse_lazy('sanitaryincident_list')
