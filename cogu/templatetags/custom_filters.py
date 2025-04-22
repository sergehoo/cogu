from django import template

register = template.Library()

@register.filter
def filter_outcome(queryset, outcome):
    return queryset.filter(outcome=outcome)


@register.filter
def filter_by_status(queryset, status):
    return queryset.filter(status=status).count()


@register.filter(name='zip_lists')
def zip_lists(a, b):
    try:
        return zip(a, b)
    except Exception:
        return []