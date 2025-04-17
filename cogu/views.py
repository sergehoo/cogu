import calendar
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.gis.db.models.functions import AsGeoJSON
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.db.models import Q, Count, F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.html import format_html
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, ListView, CreateView, DetailView, UpdateView, DeleteView, FormView
from cogu.filters import PatientFilter
from cogu.forms import SanitaryIncidentForm, PublicIncidentForm, ContactForm
from cogu.models import Patient, MajorEvent, IncidentType, SanitaryIncident, Commune, HealthRegion, VictimCare, \
    WhatsAppMessage
from django.contrib.gis.geos import Point


# Create your views here.
class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles = []
    redirect_view_if_denied = 'public_dashboard'  # nom de l’URL

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.roleemployee in self.allowed_roles

    def handle_no_permission(self):
        # Redirige vers la vue publique si le test échoue
        return redirect(self.redirect_view_if_denied)


class LandingView(FormView):
    # template_name = "pages/landing.html"
    template_name = "pages/landing.html"
    form_class = ContactForm
    success_url = reverse_lazy('landing')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Votre message a été envoyé avec succès. Nous vous contacterons bientôt!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Il y a eu une erreur dans l'envoi de votre message. Veuillez réessayer.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupération des données pour les statistiques
        # context['form'] = ContactForm()
        context['incidents_count'] = SanitaryIncident.objects.count()
        context['active_cases'] = SanitaryIncident.objects.filter(
            status='validated',
            outcome__in=['mort', 'blessure']
        ).count()
        context['regions_count'] = HealthRegion.objects.count()
        context['interventions_count'] = VictimCare.objects.count()

        # Incidents récents pour la sidebar
        context['recent_incidents'] = SanitaryIncident.objects.select_related(
            'incident_type', 'city'
        ).order_by('-date_time')[:5]

        # Données pour la carte
        context['map_incidents'] = SanitaryIncident.objects.filter(
            location__isnull=False
        ).select_related('incident_type')[:20]

        # Régions sanitaires avec leurs districts
        context['health_regions'] = HealthRegion.objects.annotate(
            district_count=Count('districts')
        ).prefetch_related('districts').order_by('name')

        return context


class PolitiqueConfidentialiteView(TemplateView):
    template_name = "pages/politique_confidential.html"



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Récupération des données pour les statistiques
        context['incidents_count'] = SanitaryIncident.objects.count()
        context['active_cases'] = SanitaryIncident.objects.filter(
            status='validated',
            outcome__in=['mort', 'blessure']
        ).count()
        context['regions_count'] = HealthRegion.objects.count()
        context['interventions_count'] = VictimCare.objects.count()

        # Incidents récents pour la sidebar
        context['recent_incidents'] = SanitaryIncident.objects.select_related(
            'incident_type', 'city'
        ).order_by('-date_time')[:5]

        # Données pour la carte
        context['map_incidents'] = SanitaryIncident.objects.filter(
            location__isnull=False
        ).select_related('incident_type')[:20]

        # Régions sanitaires avec leurs districts
        context['health_regions'] = HealthRegion.objects.annotate(
            district_count=Count('districts')
        ).prefetch_related('districts').order_by('name')

        return context


class PublicUserDashboard(LoginRequiredMixin, TemplateView):
    template_name = "pages/public/public_dashboard.html"
    login_url = 'account_login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['mesincidents'] = SanitaryIncident.objects.filter(posted_by=self.request.user).order_by('-created_at')[
                                  :5]
        return context


class PublicIncidentCreateView(LoginRequiredMixin, CreateView):
    model = SanitaryIncident
    template_name = 'pages/public/sanitaryincidentcreate.html'
    form_class = PublicIncidentForm
    success_url = reverse_lazy('public_incidentlist')

    def form_valid(self, form):
        instance = form.save(commit=False)  # Ne pas sauvegarder tout de suite
        User = get_user_model()

        if isinstance(self.request.user, User):
            instance.posted_by = self.request.user
        # instance.posted_by = self.request.user  # Assignation de l'utilisateur
        messages.success(self.request, 'Incident enregistré avec succès!')
        instance.save()
        # form.save_m2m()  # Important si tu as des champs ManyToMany
        return redirect('public_incidentlist')

    def form_invalid(self, form):
        messages.error(self.request, 'Veuillez corriger les erreurs ci-dessous :')

        # Boucle sur les champs pour afficher chaque erreur individuellement
        for field, errors in form.errors.items():
            field_label = form.fields.get(field).label if field in form.fields else field
            for error in errors:
                messages.error(self.request, format_html("<strong>{}</strong>: {}", field_label, error))

        return super().form_invalid(form)


class PublicIncidentListView(LoginRequiredMixin, ListView):
    model = SanitaryIncident
    template_name = 'pages/public/public_incident.html'
    context_object_name = 'incidents'
    paginate_by = 10
    ordering = ['-date_time']

    def get_queryset(self):
        return SanitaryIncident.objects.filter(posted_by=self.request.user).order_by(*self.ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['incidents_active'] = True  # pour activer le menu dans le template
        return context


class PublicIncidentDetailView(LoginRequiredMixin, DetailView):
    model = SanitaryIncident
    template_name = 'pages/public/public_incident_details.html'
    context_object_name = 'incidentsdetails'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['incidents_active'] = True  # pour activer le menu dans le template
        return context


class CADashborad(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    template_name = "pages/dashboard.html"
    login_url = 'account_login'
    allowed_roles = ['National', 'Regional']
    redirect_view_if_denied = 'public_dashboard'

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
        paginator = Paginator(recent_incidents, 5)
        page = request.GET.get("page")
        recent_incidents_page = paginator.get_page(page)

        # Données pour les graphiques
        regions_data = self.get_regions_data()
        monthly_data = self.get_monthly_trends()
        incident_types_data = self.get_incident_types_data()

        # Données carte
        incidents_map_data = list(
            SanitaryIncident.objects.filter(location__isnull=False)
            .annotate(
                location_json=AsGeoJSON('location')  # Transforme Point en JSON lisible
            )
            .values(
                'id',
                'incident_type__name',
                'incident_type_id',
                'city__name',
                'date_time',
                'location_json'  # à utiliser dans le JS
            )
        )

        context = {
            'available_years': list(range(2019, timezone.now().year + 1)),
            'event_labels': [e['name'] for e in self.get_event_distribution()],
            'event_data': [e['count'] for e in self.get_event_distribution()],
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
            # 'monthly_labels': [m['month'] for m in monthly_data],
            # 'monthly_data': [m['count'] for m in monthly_data],

            'monthly_labels': monthly_data['labels'],
            'monthly_current_data': monthly_data['current_year'],
            'monthly_previous_data': monthly_data['previous_year'],
            'monthly_current_label': monthly_data['current_year_label'],
            'monthly_previous_label': monthly_data['previous_year_label'],

            'incident_types_labels': [t['name'] for t in incident_types_data],
            'incident_types_data': [t['count'] for t in incident_types_data],
            'incidents_map_data': incidents_map_data,

        }

        return self.render_to_response(context)

    def get_monthly_trends(self):
        from collections import defaultdict
        import calendar

        current_year = timezone.now().year
        previous_year = current_year - 1

        MONTHS_FR = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                     "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

        current_data = defaultdict(int)
        previous_data = defaultdict(int)

        incidents = SanitaryIncident.objects.filter(
            date_time__year__in=[current_year, previous_year]
        ).annotate(
            month=F('date_time__month'),
            year=F('date_time__year')
        ).values('month', 'year').annotate(count=Count('id'))

        for entry in incidents:
            if entry['year'] == current_year:
                current_data[entry['month']] = entry['count']
            elif entry['year'] == previous_year:
                previous_data[entry['month']] = entry['count']

        monthly_labels = [f"{MONTHS_FR[m]}" for m in range(1, 13)]
        current_year_data = [current_data[m] for m in range(1, 13)]
        previous_year_data = [previous_data[m] for m in range(1, 13)]

        return {
            'labels': monthly_labels,
            'current_year': current_year_data,
            'previous_year': previous_year_data,
            'current_year_label': current_year,
            'previous_year_label': previous_year
        }

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

    def get_event_distribution(self):
        return (
            SanitaryIncident.objects
            .filter(event__isnull=False)
            .values(name=F('event__name'))
            .annotate(count=Count('id'))
            .order_by('-count')
        )

    def get_incident_types_data(self):
        return (
            SanitaryIncident.objects
            .values(name=F('incident_type__name'))
            .annotate(count=Count('id'))
            .order_by('-count')
        )


class PatientListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = Patient
    template_name = 'patient/list.html'
    context_object_name = 'patients'
    allowed_roles = ['National', 'Regional']
    paginate_by = 20
    ordering = ['-created_at']
    filterset_class = PatientFilter

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.roleemployee in ['National', 'Regional']

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


class PatientCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Patient
    template_name = 'patient/create.html'
    allowed_roles = ['National', 'Regional']
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


class PatientDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = Patient
    template_name = 'patient/detail.html'
    allowed_roles = ['National', 'Regional']
    context_object_name = 'patient'
    slug_field = 'code_patient'
    slug_url_kwarg = 'code_patient'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Détails Patient - {self.object.code_patient}"
        return context


class PatientUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Patient
    template_name = 'patient/update.html'
    fields = '__all__'
    slug_field = 'code_patient'
    slug_url_kwarg = 'code_patient'
    success_url = reverse_lazy('patient_list')
    allowed_roles = ['National', 'Regional']

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Patient {self.object} mis à jour avec succès!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Modifier Patient - {self.object.code_patient}"
        return context


class PatientDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Patient
    template_name = 'patient/delete.html'
    slug_field = 'code_patient'
    slug_url_kwarg = 'code_patient'
    success_url = reverse_lazy('patient_list')
    allowed_roles = ['National', 'Regional']

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Patient {self.object} supprimé avec succès!")
        return response


class MajorEventListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = MajorEvent
    template_name = 'majorevent/list.html'
    context_object_name = 'events'
    paginate_by = 20
    ordering = ['-start_date']
    allowed_roles = ['National', 'Regional']


class MajorEventGridView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = MajorEvent
    template_name = 'majorevent/event_grid.html'
    context_object_name = 'events'
    paginate_by = 20
    # ordering = ['-start_date']
    allowed_roles = ['National', 'Regional']

    def get_queryset(self):
        now = timezone.now()
        return MajorEvent.objects.filter(start_date__gte=now).order_by('start_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for event in context['events']:
            event.mort_count = event.sanitaryincident_set.filter(outcome='mort').count()
            event.blessure_count = event.sanitaryincident_set.filter(outcome='blessure').count()
            event.sauve_count = event.sanitaryincident_set.filter(outcome='sauvé').count()
            event.incident_count = event.sanitaryincident_set.all().count()
        return context


class MajorEventCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = MajorEvent
    template_name = 'majorevent/event_create.html'
    fields = '__all__'
    success_url = reverse_lazy('majorevent_list')
    allowed_roles = ['National', 'Regional']


class MajorEventDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = MajorEvent
    template_name = 'majorevent/event_detail.html'
    context_object_name = 'event'
    allowed_roles = ['National', 'Regional']


class MajorEventUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = MajorEvent
    template_name = 'majorevent/event_update.html'
    fields = '__all__'
    success_url = reverse_lazy('majorevent_list')
    allowed_roles = ['National', 'Regional']


class MajorEventDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = MajorEvent
    template_name = 'majorevent/event_delete.html'
    success_url = reverse_lazy('majorevent_list')
    allowed_roles = ['National', 'Regional']


class IncidentTypeListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = IncidentType
    template_name = 'incidenttype/incidentlist.html'
    context_object_name = 'types'
    ordering = ['name']
    allowed_roles = ['National', 'Regional']


class IncidentTypeCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = IncidentType
    template_name = 'incidenttype/incidentcreate.html'
    fields = '__all__'
    success_url = reverse_lazy('incidenttype_list')
    allowed_roles = ['National', 'Regional']


class IncidentTypeDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = IncidentType
    template_name = 'incidenttype/incidentdetail.html'
    context_object_name = 'type'
    allowed_roles = ['National', 'Regional']


class IncidentTypeUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = IncidentType
    template_name = 'incidenttype/incidentupdate.html'
    fields = '__all__'
    success_url = reverse_lazy('incidenttype_list')
    allowed_roles = ['National', 'Regional']


class IncidentTypeDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = IncidentType
    template_name = 'incidenttype/incidentdelete.html'
    success_url = reverse_lazy('incidenttype_list')
    allowed_roles = ['National', 'Regional']


class SanitaryIncidentListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/list.html'
    context_object_name = 'incidents'
    paginate_by = 10
    ordering = ['-date_time']
    allowed_roles = ['National', 'Regional']

    def get_queryset(self):
        return SanitaryIncident.objects.filter(status='validated').order_by(*self.ordering)


class IncidentToValidListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/non_valid_list.html'
    context_object_name = 'incidents'
    paginate_by = 10
    ordering = ['-date_time']
    allowed_roles = ['National', 'Regional']

    def get_queryset(self):
        return SanitaryIncident.objects.exclude(status='validated').order_by(*self.ordering)


class SanitaryIncidentCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/create.html'
    form_class = SanitaryIncidentForm
    success_url = reverse_lazy('sanitaryincident_list')
    allowed_roles = ['National', 'Regional']

    def form_valid(self, form):
        # 1. Sauvegarde sans commit pour ajouter l'événement
        incident = form.save(commit=False)

        # 2. Recherche d’un événement en cours à la date de l’incident
        incident_date = form.cleaned_data.get('date_time')

        matching_event = MajorEvent.objects.filter(
            start_date__lte=incident_date,
            end_date__gte=incident_date
        ).first()

        if matching_event:
            incident.event = matching_event

        # 3. Ajout de l'utilisateur qui poste si besoin
        incident.posted_by = self.request.user if self.request.user.is_authenticated else None

        # 4. Sauvegarde finale
        incident.save()
        form.save_m2m()

        messages.success(self.request, 'Incident enregistré avec succès !')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Veuillez corriger les erreurs ci-dessous :')

        # Boucle sur les champs pour afficher chaque erreur individuellement
        for field, errors in form.errors.items():
            field_label = form.fields.get(field).label if field in form.fields else field
            for error in errors:
                messages.error(self.request, format_html("<strong>{}</strong>: {}", field_label, error))

        return super().form_invalid(form)


@require_POST
def validate_incident(request, pk):
    incident = get_object_or_404(SanitaryIncident, pk=pk)
    incident.status = 'validated'
    incident.save()
    messages.success(request, "✅ Incident validé avec succès.")
    return redirect('sanitaryincident_detail', pk=pk)


@require_POST
def reject_incident(request, pk):
    incident = get_object_or_404(SanitaryIncident, pk=pk)
    incident.status = 'rejected'
    incident.save()
    messages.warning(request, "🚫 Incident rejeté.")
    return redirect('sanitaryincident_detail', pk=pk)


class IncidentMapView(RoleRequiredMixin, TemplateView):
    template_name = 'sanitaryincident/incident_map.html'
    allowed_roles = ['National', 'Regional']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        incidents = SanitaryIncident.objects.all()
        context['incidents_geojson'] = serialize('geojson', incidents,
                                                 geometry_field='location',
                                                 fields=(
                                                     'id', 'incident_type__name', 'status', 'date_time', 'city__name'))
        return context

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            incidents = SanitaryIncident.objects.all()
            data = {
                'type': 'FeatureCollection',
                'features': [{
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [incident.location.x, incident.location.y] if incident.location else None
                    },
                    'properties': {
                        'id': incident.id,
                        'type': incident.incident_type.name,
                        'status': incident.get_status_display(),
                        'date': incident.date_time.strftime('%d/%m/%Y %H:%M'),
                        'location': incident.city.name if incident.city else 'Inconnu',
                        'outcome': incident.get_outcome_display(),
                        'people_involved': incident.number_of_people_involved,
                        'icon': self.get_incident_icon(incident)
                    }
                } for incident in incidents if incident.location]
            }
            return JsonResponse(data)
        return super().get(request, *args, **kwargs)

    def get_incident_icon(self, incident):
        if incident.status == 'validated':
            return 'validated-icon'
        elif incident.status == 'rejected':
            return 'rejected-icon'
        return 'pending-icon'


class SanitaryIncidentDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/detail.html'
    context_object_name = 'incident'
    allowed_roles = ['National', 'Regional']

    def get_queryset(self):
        return (
            SanitaryIncident.objects
            .select_related('message', 'city', 'incident_type')
            .prefetch_related('media', 'patients_related')
            # .filter(status='validated')  # filtre si on veut afficher seulement les incidents validés
        )


class SanitaryIncidentUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/update.html'
    form_class = SanitaryIncidentForm
    success_url = reverse_lazy('sanitaryincident_list')
    allowed_roles = ['National', 'Regional']

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


class SanitaryIncidentDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = SanitaryIncident
    template_name = 'sanitaryincident/delete.html'
    success_url = reverse_lazy('sanitaryincident_list')
    allowed_roles = ['National', 'Regional']


class WhatsAppMessageListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = WhatsAppMessage
    template_name = 'pages/whatsapp/messages_list.html'
    context_object_name = 'messages'
    paginate_by = 20
    ordering = ['-timestamp']
    allowed_roles = ['National', 'Regional']

    def get_queryset(self):
        return WhatsAppMessage.objects.all().order_by(*self.ordering)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre message a été envoyé avec succès. Nous vous contacterons bientôt!")
            return redirect('contact')  # Replace with your actual contact URL name
        else:
            messages.error(request, "Il y a eu une erreur dans l'envoi de votre message. Veuillez réessayer.")
    else:
        form = ContactForm()

    return render(request, 'pages/landing.html', {'form': form})
