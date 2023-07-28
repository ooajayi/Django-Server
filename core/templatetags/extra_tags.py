from dateutil.relativedelta import *
from datetime import date

from django import template
# from django.db.models import Q

register = template.Library() 

"""
today = date.today()
dob = date(1982, 7, 5)
age = relativedelta(today, dob)

# relativedelta(years=+33, months=+11, days=+16)
"""

@register.filter("is_list")
def is_list(data):
    """
    usage example {{ data|is_list }}
    """
    return type(data) == list


@register.filter("get_value_from_dict")
def get_value_from_dict(data, key):
    """
    usage example {{ your_dict|get_value_from_dict:your_key }}
    """
    try:
        value = ""
        for k, v in data.items():
            if k == key:
                value = data[k]
                break
        return value
    except AttributeError:
        return data


@register.filter(name='dict_key')
def dict_key(d, k):
    '''Returns the given key from a dictionary.'''
    return d[k]


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
