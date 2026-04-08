from django import template

register = template.Library()

@register.filter(name='get_val')
def get_val(dictionary, key):
    return dictionary.get(key, 0)