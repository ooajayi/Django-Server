import json
import operator

from functools import reduce

import logging
import traceback
from parser import ParserError
from dateutil import parser
from django.conf import settings

from django.core.paginator import EmptyPage, Paginator
from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required, permission_required)
from django.contrib.auth.mixins import (
    LoginRequiredMixin, PermissionRequiredMixin)
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
from core.forms.classified import StudioEventForm
from core.forms.registration import StudioForm
from core.models.classifieds import StudioEvent
from core.models.common import Attachment, Genre, Location
from core.models.user import (
    Studio, StudioLocation, UserProfile)

core_logger = logging.getLogger(__name__)


class StudiosHtmxView(LoginRequiredMixin, generic.TemplateView):
    template_name = "components/htmx/studios.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        search_str: str = self.request.GET.get("srch", "")
        loc_search_str: str = self.request.GET.get("location", "")
        page: int = self.request.GET.get("page", 1)
        init_load: int = self.request.GET.get("initLoad", 1)
        page_len: int = self.request.GET.get("page_len", 15)
        genres = self.request.GET.getlist("genres", [])

        context["studios"] = get_studios_to_display(
            search_str, page=page, pg_len=page_len,
            genres=genres, loc_search=loc_search_str
        )
        context["page"] = page
        context["init_load"] = init_load

        context["genres"] = genres
        context["srch"] = search_str
        context["location"] = loc_search_str

        return context


class StudiosListView(LoginRequiredMixin, generic.ListView):
    template_name = 'home/studios.html'
    model = Studio

    def get_queryset(self):
        return Studio.objects.filter(active=True)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context['timezones'] = TIME_ZONE_CHOICES
        context['user_email'] = get_user_primary_email(self.request.user)

        return context


def get_studios_to_display(srch_val="", loc_search="", page=1, pg_len=20,
                           genres=[]):
    values = srch_val.split()
    location_strs = loc_search.split()
    query = None
    location_query = None

    if values:
        query = reduce(operator.and_,
                       [Q(name__icontains=v) | Q(email__icontains=v) 
                        | Q(bio__icontains=v) 
                        | Q(profile__user__username__icontains=v)
                        | Q(profile__alt_name__icontains=v)
                        | Q(profile__display_name__icontains=v)
                        for v in values])

    if location_strs:
        location_query = reduce(operator.and_,
                                [Q(address__icontains=v) 
                                 | Q(city__icontains=v)
                                 | Q(province__icontains=v)
                                 | Q(country__icontains=v)
                                 | Q(postal_code__icontains=v)
                                 for v in location_strs])

    studio_objs = Studio.objects.filter(active=True)

    objs = studio_objs.filter(query) if query is not None else studio_objs

    if location_query is not None:
        objs = studio_objs.filter(location_query)
    else:
        objs = studio_objs

    results = objs.distinct().prefetch_related(
        "genres", "likes", "dislikes", "followers", "files"
    )
    if genres:
        results = results.filter(genres__in=genres)

    results = results.order_by("-created_at")
    studios_paginator = Paginator(results, pg_len)

    try:
        studios_list = studios_paginator.page(page)
    except EmptyPage:
        studios_list = studios_paginator.page(studios_paginator.num_pages)

    return studios_list


def _list_studio_events(studio_pk, start_date, end_date) -> list:
    """
    List of the specified studio's event based on the 
    based on the start and end dates.
    :params: studio_pk - primary key of studio to search
    :params: start_date - datetime obj for when to begin search
    :params: end_date - datetime obj for when to end search
    :return: list of events that can be used in full calendar
    """

    events = []

    print(f"Studio {studio_pk}\n startDate={start_date}\n endDate={end_date}")

    objs = StudioEvent.objects.filter(
        Q(start_dt__gte=start_date,)
        | Q(start_dt__lt=end_date),
        active=True, studio_id=studio_pk
    )

    for event_obj in objs:
        events.append({
            "id": event_obj.id,
            "eventId": event_obj.id,
            "title": event_obj.title,
            "frequency": event_obj.freq,
            "start": event_obj.start_dt,
            "end": event_obj.end_dt,
            "classNames": ["dcc-cursor"],
            "description": event_obj.description,
            # "tz": event_obj.studio.locationtimezone
        })

    return events


@login_required
def list_studio_events(request):
    studio_id = request.GET.get("studio", -1)
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
        events = _list_studio_events(studio_id, from_dt, end_dt)

    return JsonResponse({
        "events": events
    })


@login_required
def create_studio_event(request):
    if request.method != "POST":
        return JsonResponse({
            "isValid": False,
            "msg": gettext("Invalid request type")
        })

    is_valid = False
    msg = gettext("Unable to create event, please try again!")
    studio_pk = request.POST.get("studio", -1)
    studio_event_form = StudioEventForm(request.POST)

    if studio_event_form.is_valid():
        is_valid = True
        submitted_form = studio_event_form.save(commit=False)
        submitted_form.active = True
        submitted_form.save()
        msg = gettext("Event created successfully!")

    return JsonResponse({
        "isValid": is_valid,
        "msg": msg,
        "nonFieldErrors": studio_event_form.non_field_errors(),
        "errors": studio_event_form.errors.get_json_data()
    })


@login_required
def studio_event_details(request, *args, **kwargs):
    is_valid = False
    event_pk = kwargs['pk']

    if request.method == "GET":
        try:
            event_obj = StudioEvent.objects.get(id=event_pk)
            start_dt_str = event_obj.start_dt.strftime("%Y-%m-%dT%H:%M")
            end_dt_str = event_obj.end_dt.strftime("%Y-%m-%dT%H:%M")
            freq_end_dt_str = ""

            if event_obj.freq_end:
                freq_end_dt_str  = event_obj.freq_end.strftime("%Y-%m-%d")

            event_details = {
                "id": event_obj.id,
                "title": event_obj.title,
                "description": event_obj.description,
                "frequency": event_obj.freq,
                "start": start_dt_str,
                "end": end_dt_str,
                "image": event_obj.image.url if event_obj.image else "",
                "frequency_end_dt": freq_end_dt_str,
                "active": event_obj.active
            }
            msg = gettext("Studio data found")
            is_valid = True
        except StudioEvent.DoesNotExist:
            msg = gettext("Studio event not found!")
            event_details = {}

        return JsonResponse({
            "isValid": is_valid,
            "msg": msg,
            "event": event_details
        })
    elif request.method == "POST":
        action = request.POST.get("action", "UPDATE")
        if action == "DELETE":
            errors = ""
            try:
                event_obj = StudioEvent.objects.get(id=event_pk)
                event_obj.active= False
                event_obj.save()
                is_valid = True
                msg = gettext("Schedule item deleted")
            except StudioEvent.DoesNotExist:
                errors = gettext("Schedule item does not exist!")

            return JsonResponse({
                "isValid": is_valid,
                "errors": errors
            })
        else:
            is_new_event = False
            if int(request.POST['pk']) == -1:
                content_form = StudioEventForm(data=request.POST)
                content_obj = content_form.save(commit=False)
                is_new_event = True
            else:
                content_obj = StudioEvent.objects.get(
                    pk=int(request.POST['pk']))
                content_form = StudioEventForm(data=request.POST,
                                               instance=content_obj)

            is_valid = content_form.is_valid()
            if is_valid:
                content_obj.active = True
                if is_new_event:
                    msg = gettext("Event created successfully!")
                else:
                    msg = gettext("Event updated successfully!")
                content_obj.save()

            return JsonResponse({
                "isValid": is_valid,
                "nonFieldErrors": content_form.non_field_errors(),
                "errors": content_form.errors.get_json_data(),
                "msg": content_form.errors.get_json_data()
            })
    else:
        return JsonResponse({
            "isValid": is_valid,
            "msg": gettext("Invalid request type!")
        })


def create_json_ready_studio_obj(obj):
    obj_genres = list(
        obj.genres.filter(active=True).values_list('id', flat=True)
    )

    studio = {
        "id": obj.id,
        "name": obj.name,
        "bio": obj.bio,
        "phone": obj.phone,
        "email": obj.email,
        "facebook": obj.facebook,
        "instagram": obj.instagram,
        "twitter": obj.twitter,
        "tiktok": obj.tiktok,
        "youtube": obj.youtube,
        "likes": obj.likes.count(),
        "location": obj.display_loc_str(),
        "genres": obj_genres,
        "address": obj.address,
        "city": obj.city,
        "province": obj.province,
        "country": obj.country,
        "postal_code": obj.postal_code,
    }

    return studio


def _list_my_studios(profile)-> list:
    """
    List of the studios for the logged in user if they are a studio admin.
    :param: profile: profile object for which to grab studios
    :returns: list of objects
    """
    studios = []

    objs = Studio.objects.filter(active=True, profile=profile)

    for obj in objs:
        studios.append(create_json_ready_studio_obj(obj))

    return studios


@login_required
def my_studios_list(request):
    profile = request.user.get_user_profile()
    studios = []

    if profile and profile.type == "studio":
        studios = _list_my_studios(profile)

    return JsonResponse({
        "studios": studios
    })


@login_required
def my_studio_details(request, *args, **kwargs):
    is_valid = False

    if request.method == "GET":
        try:
            studio_pk = request.GET.get("pk")
            obj = Studio.objects.get(id=studio_pk)
            studio = create_json_ready_studio_obj(obj)
            msg = gettext("Studio found")
            is_valid = True
        except Studio.DoesNotExist:
            msg = gettext("Studio not found!")
            studio = {}

        return JsonResponse({
            "isValid": is_valid,
            "msg": msg,
            "studio": studio
        })
    elif request.method == "POST":
        action = request.POST.get("action", "UPDATE")
        if action == "DELETE":
            pass
        else:
            is_new_studio = False
            msg = gettext("An error occurred! Unable to save.")
            if int(request.POST['pk']) == -1:
                content_form = StudioForm(data=request.POST)
                content_obj = content_form.save(commit=False)
                is_new_studio = True
            else:
                content_obj = Studio.objects.get(pk=int(request.POST['pk']))
                content_form = StudioForm(data=request.POST,
                                          instance=content_obj)

            is_valid = content_form.is_valid()
            if is_valid:
                content_obj.active = True
                if is_new_studio:
                    msg = gettext("Studio created successfully!")
                else:
                    msg = gettext("Studio updated successfully!")
                content_obj.save()

                studio_files = []
                # for f in request.FILES.getlist('files'):
                for filename, file in request.FILES.items():
                    attachment = Attachment.objects.create(
                        label=filename, file=file,
                        created_by=request.user,
                        active=True
                    )
                    content_obj.files.add(attachment)
                    studio_files.append(attachment.id)

            return JsonResponse({
                "isValid": is_valid,
                "msg": msg,
                "nonFieldErrors": content_form.non_field_errors(),
                "errors": content_form.errors.get_json_data(),
            })
    else:
        return JsonResponse({
            "isValid": False,
            "msg": gettext("Invalid request type!") 
        })


def get_top_studio_genres(nums=6):
    top_studio_genres = Genre.objects.filter(
        active=True, studio__active=True
    ).annotate(
        studio_count=Count('studio__genres')
    ).order_by('-studio_count')[0:nums]

    if not top_studio_genres:
        top_studio_genres = Genre.objects.filter(
            active=True
        )[0:nums]

    return top_studio_genres
