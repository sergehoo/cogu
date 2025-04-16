from django import template

register = template.Library()

@register.filter
def filter_outcome(queryset, outcome):
    return queryset.filter(outcome=outcome)