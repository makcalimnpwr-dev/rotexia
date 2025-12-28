from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def split(value, delimiter=','):
    """String'i delimiter'e göre böler"""
    if not value:
        return []
    return [item.strip() for item in str(value).split(delimiter) if item.strip()]