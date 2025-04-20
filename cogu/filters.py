from django import template

import django_filters

from cogu.models import Patient

register = template.Library()


class PatientFilter(django_filters.FilterSet):
    date_naissance = django_filters.DateFromToRangeFilter(field_name='date_naissance')
    created_at = django_filters.DateFromToRangeFilter(field_name='created_at')
    age_min = django_filters.NumberFilter(method='filter_by_age_min')
    age_max = django_filters.NumberFilter(method='filter_by_age_max')

    class Meta:
        model = Patient
        fields = {
            'sexe': ['exact'],
            'commune': ['exact'],
            'quartier': ['icontains'],
            'status': ['exact'],
            'gueris': ['exact'],
            'decede': ['exact'],
            'patient_mineur': ['exact'],
        }

    def filter_by_age_min(self, queryset, name, value):
        from datetime import date, timedelta
        max_date = date.today() - timedelta(days=int(value) * 365)
        return queryset.filter(date_naissance__lte=max_date)

    def filter_by_age_max(self, queryset, name, value):
        from datetime import date, timedelta
        min_date = date.today() - timedelta(days=int(value) * 365)
        return queryset.filter(date_naissance__gte=min_date)


@register.filter
def filter_by_status(queryset, status):
    return queryset.filter(status=status).count()
