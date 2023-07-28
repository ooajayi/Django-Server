import json
import operator

from functools import reduce

import logging
import traceback
from parser import ParserError
from dateutil import parser
from django.conf import settings

# from django.core.paginator import EmptyPage, Paginator
# from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required, permission_required)
# from django.contrib.auth.mixins import (
#     LoginRequiredMixin, PermissionRequiredMixin)
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.log import request_logger as django_request_logger
from django.utils.translation import gettext
from django.views import generic

from common.constants import TIME_ZONE_CHOICES
from common.email_validation import validate_email
from common.func_utils import get_user_primary_email
from core.models.user import Studio
from core.models.classifieds import Event, Listing, StudioEvent
from core.views.studio import _list_studio_events


core_logger = logging.getLogger(__name__)


def _list_events(start_date, end_date) -> list:
    """
    List of the events based on the start and end dates provided.
    :params: start_date - datetime obj for when to begin search
    :params: end_date - datetime obj for when to end search
    :return: list of events that can be used in full calendar
    """

    events = []

    objs = Event.objects.filter(
        Q(start_dt__gte=start_date,)
        | Q(start_dt__lt=end_date),
        active=True
    )

    for event_obj in objs:
        events.append({
            "id": event_obj.id,
            "eventId": event_obj.id,
            "title": event_obj.title,
            "frequency": event_obj.freq,
            "start": event_obj.start_dt,
            "end": event_obj.end_dt,
            "classNames": ["dcc-cursor", "dcc-reg-event"],
            "description": event_obj.description,
            # "tz": event_obj.studio.locationtimezone
        })

    return events


@login_required
def list_events(request):
    from_dt = request.GET.get("start")
    end_dt = request.GET.get("end")
    is_valid = True
    events = []

    try:
        from_dt = parser.parse(from_dt)
    except ParserError:
        from_dt = parser.isoparse(from_dt)
    except Exception:
        is_valid = False
        msg = gettext("Invalid start datetime, please validate")

    try:
        end_dt = parser.parse(end_dt)
    except ParserError:
        end_dt = parser.isoparse(end_dt)
    except Exception:
        is_valid = False
        msg = gettext("Invalid end datetime, please validate")

    if is_valid:
        msg = gettext("Events returned!")
        events = _list_events(from_dt, end_dt)

    return JsonResponse({
        "events": events
    })


@login_required
def list_all_studio_events(request):
    from_dt = request.GET.get("start")
    end_dt = request.GET.get("end")
    is_valid = True
    events = []
    studios = Studio.objects.filter(active=True)

    try:
        from_dt = parser.parse(from_dt)
    except ParserError:
        from_dt = parser.isoparse(from_dt)
    except Exception:
        is_valid = False
        msg = gettext("Invalid start datetime, please validate")

    try:
        end_dt = parser.parse(end_dt)
    except ParserError:
        end_dt = parser.isoparse(end_dt)
    except Exception:
        is_valid = False
        msg = gettext("Invalid end datetime, please validate")

    if is_valid:
        msg = gettext("Events returned!")
        for studio in studios:
            events += _list_studio_events(studio.id, from_dt, end_dt)

    return JsonResponse({
        "events": events
    })


@login_required
def events_calendar(request):
    return render(request, 'home/events_calendar.html')
