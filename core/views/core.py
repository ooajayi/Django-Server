import json

import logging
import requests
import traceback
import operator

from functools import reduce

from django.core.paginator import EmptyPage, Paginator
from django.conf import settings

from django.contrib import messages
from django.contrib.auth import (
    authenticate, logout, login, update_session_auth_hash)
from django.contrib.auth.decorators import (
    login_required, permission_required)
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import (
    LoginRequiredMixin, PermissionRequiredMixin)
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.text import slugify
from django.utils import timezone
from django.utils.log import request_logger as django_request_logger
from django.utils.translation import gettext
from django.views import generic

from common.constants import TIME_ZONE_CHOICES
from common.email_validation import validate_email
from common.func_utils import get_user_primary_email
from core.forms.core import GenreForm, LocationForm
from core.forms.registration import (
    EmailSubscriberForm, UserUpdateForm, UserProfileForm)
from core.models.user import (
    EmailSubscribers, UserProfile, Studio, StudioLocation)
from core.models.common import Genre, Location

from taggit.models import Tag


core_logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'base.html')

def homepage(request):
    return render(request, 'base.html')

def handler404(request, exception):
    return render(request, '404.html')

def handler500(request, *args, **kwargs):
    context = {}
    context["error_msg"] = "An internal server error occurred."
    context["stack_trace"] = traceback.format_exc()

    django_request_logger.exception("Internal Server Error: %s", request.path)

    return render(request, "500.html", context)


def handle_contact_form(request):
    valid = False
    msg = ""

    if request.method == "GET":
        return render(
            request, 'contact.html', {}
        )
    else:
        if request.method == "POST":
            form = ContactForm(request.POST)
            if form.is_valid():
                ''' Begin reCAPTCHA validation '''
                recaptcha_response = request.POST.get('g-recaptcha-response')
                data = {
                    'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response
                }
                r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
                result = r.json()
                ''' End reCAPTCHA validation '''

                if result['success']:
                    form.save()
                    valid = True
                    msg = gettext("Form successfully submitted!")
                else:
                    msg = gettext("Invalid reCAPTCHA. Please try again.")
        
        return JsonResponse({
            "isValid": valid,
            "msg": msg,
            "errors": json.dumps(form.errors)
        })


def user_profile(request):
    return render(request, 'users/profile.html')


class LandingPageView(generic.ListView):
    template_name = 'landing.html'
    model = UserProfile

    """def get_queryset(self):
        if self.request.user.is_authenticated:
            return redirect('/')
        else:
            return None"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        return context


class IndexView(generic.ListView):
    # template_name = 'uf_home_alt.html'
    template_name = 'home/index.html'
    model = UserProfile

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect('/home')
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.get_user_profile()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        prof_obj = self.request.user.get_user_profile()
        ctry = None
        province = None

        if prof_obj:
            ctry = prof_obj.country
            province = prof_obj.province

        # if user is dancer/creator need to return dancers/studios/creators in the same 
        # country/province, allow button to display all dancers in the template
        # Have listings for that country/province 
        profiles = UserProfile.objects.filter(
            Q (country__iexact=ctry, province__iexact=province)
            | Q(country__isnull=True, province__isnull=True),
            active=True,
        )
        dancers = profiles.filter(type="dancer")
        creators = profiles.filter(type="creator")

        studios = Studio.objects.filter(
            # Q (country__iexact=ctry, province__iexact=province)
            #| Q(country__isnull=True, province__isnull=True),
            active=True,
        )

        # TODO: add pagination

        context['studios'] = studios
        context['dancers'] = dancers
        context['creators'] = creators
        context['listings'] = []  # Notification feed

        return context


class ProfileView(generic.ListView):
    # template_name = 'uf_home_alt.html'
    template_name = 'base.html'
    model = UserProfile

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return UserProfile.objects.filter(user=self.request.user).first()
        else:
            return None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        
        return context


class MyProfileView(LoginRequiredMixin, generic.DetailView):
    template_name = 'users/profile.html'
    model = UserProfile

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user).first()

    def get(self, request):
        profile = self.request.user.get_user_profile()
        genres = Genre.objects.filter(active=True)

        if not profile:
            template_name = 'users/profile_setup.html'
            context={
                'genres': genres,
                'timezones': TIME_ZONE_CHOICES,
            }
            return render(request, template_name, context)

        if profile.type == "studio":
            return redirect('core:my_studio')

        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

        context = {
            'profile': profile,
            'user_form': user_form,
            'timezones': TIME_ZONE_CHOICES,
            'profile_form': profile_form,
            'user_email': get_user_primary_email(request.user),
            'my_genres': list(profile.genres.filter(
                active=True).values_list('id', flat=True)),
            'password_change_form': PasswordChangeForm(request.user)
        }

        messages.success(request, 'Loading your profile')

        return render(request, 'users/profile.html', context)

    def post(self, request):
        try:
            profile_obj = request.user.get_user_profile()
            user_form = UserUpdateForm(
                request.POST, 
                instance=request.user
            )
            profile_form = UserProfileForm(
                request.POST,
                request.FILES,
                instance=profile_obj
            )

            if profile_obj:
                if user_form.is_valid() and profile_form.is_valid():
                    user_form.save()
                    profile_form.save()

                    messages.success(
                        request,
                        gettext('Your profile has been updated successfully')
                    )

                    return redirect('core:my_profile')
                else:
                    context = {
                        'user_form': user_form,
                        'profile_form': profile_form
                    }
                    messages.error(request, 'Error updating your profile')

                    return render(request, 'users/profile.html', context)
            else:
                messages.error(request, 'Invalid profile')

                return render(request, 'users/profile.html')
        except Exception:
            return render(request, 'users/profile.html')


class ProfilesListView(LoginRequiredMixin, generic.ListView):
    template_name = 'home/dancers.html'
    model = UserProfile

    def get_queryset(self):
        return UserProfile.objects.filter(
            active=1, type__in=["dancer", "creator"])

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context['timezones'] = TIME_ZONE_CHOICES
        context['user_email'] = get_user_primary_email(self.request.user)

        return context


class CreatorsListView(LoginRequiredMixin, generic.ListView):
    template_name = 'home/creators.html'
    model = UserProfile

    def get_queryset(self):
        return UserProfile.objects.filter(
            active=1, type="creator")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context['timezones'] = TIME_ZONE_CHOICES
        context['user_email'] = get_user_primary_email(self.request.user)

        return context


class MyStudioView(LoginRequiredMixin, generic.DetailView):
    template_name = 'users/studio.html'
    model = UserProfile

    def get_queryset(self):
        return UserProfile.objects.filter(
            user=self.request.user, type="studio").first()

    def get(self, request):
        profile = self.request.user.get_user_profile()
        primary_email = request.user.emailaddress_set

        if not profile:
            template_name = 'users/profile_setup.html'
            context={
                'timezones': TIME_ZONE_CHOICES,
            }
            return render(request, template_name, context)

        if profile.type in ["dancer", "creator"]:
            return redirect('core:my_profile')
 
        profile_form = UserProfileForm(instance=profile)

        context = {
            'profile': profile,
            'studio': profile.get_studio(),
            'studios': Studio.objects.filter(active=True, profile=profile),
            'timezones': TIME_ZONE_CHOICES,
            'profile_form': profile_form,
            'my_genres': list(profile.genres.filter(
                active=True).values_list('id', flat=True)),
            'studio_locs': profile.studio_locations(),
            'user_email': get_user_primary_email(request.user),
            'password_change_form': PasswordChangeForm(request.user)
        }

        return render(request, 'users/studio.html', context)

    def post(self, request):
        profile_obj = request.user.get_user_profile()
        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile_obj
        )

        if profile_obj:
            if profile_form.is_valid():
                profile_form.save()

                messages.success(
                    request,
                    gettext('Your studio profile has been updated successfully')
                )

                return redirect('core:my_studio')
            else:
                context = {
                    'profile_form': profile_form
                }
                messages.error(request, 'Error updating your studio profile')

                return render(request, 'users/studio.html', context)
        else:
            messages.error(request, gettext('Invalid studio record'))

            return render(request, 'users/studio.html', context)


class DancersHtmxView(LoginRequiredMixin, generic.TemplateView):
    template_name = "components/htmx/dancers.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        search_str: str = self.request.GET.get("dancer_srch", "")
        page: int = self.request.GET.get("page", 1)
        init_load: int = self.request.GET.get("initLoad", 1)
        page_len: int = self.request.GET.get("page_len", 20)
        genres = self.request.GET.getlist("dancer_genres", [])

        context["dancers"] = get_profs_to_display(
            search_str, page=page, pg_len=page_len,
            prof_type="dancer", genres=genres
        )
        context["page"] = page
        context["init_load"] = init_load

        context["genres"] = genres
        context["srch"] = search_str

        return context


class CreatorsHtmxView(LoginRequiredMixin, generic.TemplateView):
    template_name = "components/htmx/creators.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        search_str: str = self.request.GET.get("creator_srch", "")
        page: int = self.request.GET.get("page", 1)
        init_load: int = self.request.GET.get("initLoad", 1)
        page_len: int = self.request.GET.get("page_len", 20)
        genres = self.request.GET.getlist("creator_genres", [])

        context["creators"] = get_profs_to_display(
            search_str, page=page, pg_len=page_len,
            prof_type="creator", genres=genres
        )
        context["page"] = page
        context["init_load"] = init_load

        context["genres"] = genres
        context["srch"] = search_str

        return context


def get_profs_to_display(srch_val="", page=1, pg_len=20, 
                           prof_type="dancer", genres=[]):
    values = srch_val.split()
    query = None

    if values:
        query = reduce(operator.and_,
                       [Q(full_name__icontains=v) 
                        | Q(bio__icontains=v) | Q(user__email__icontains=v)
                        | Q(user__username__icontains=v)
                        | Q(alt_name__icontains=v)
                        | Q(display_name__icontains=v)
                        for v in values])

    dancer_objs = UserProfile.objects.filter(active=True, type=prof_type)
    objs = dancer_objs.filter(query) if query is not None else dancer_objs

    results = objs.distinct().prefetch_related(
        "genres", "likes", "dislikes", "followers"
    )
    if genres:
        results = results.filter(genres__in=genres)

    results = results.order_by("-created_at")
    dancers_paginator = Paginator(results, pg_len)

    try:
        dancers_list = dancers_paginator.page(page)
    except EmptyPage:
        dancers_list = dancers_paginator.page(dancers_paginator.num_pages)

    return dancers_list


@login_required
def setup_profile(request):
    form = UserProfileForm()

    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.full_name = request.user.get_user_fullname()
            profile.user = request.user
            profile.created_by = request.user
            profile.active = True
            profile.is_verified = True
            profile.save()
            messages.success(request, gettext("Profile saved!"))

            return redirect('core:profile')

    return render(
        request, 'users/profile.html', 
        {'form': form}
    )


@login_required
def active_genres(request):
    if request.method == "GET":
        genres = Genre.objects.filter(
            active=1
        ).values_list("id", "slug", "name")
    
        return JsonResponse({
            "isValid": True,
            "genres": list(genres)
        })
    else:
        if request.method == "POST":
            form = GenreForm(request.POST)
            genre_id = -1
            genre_name = ""
            msg = gettext("Form validation failed!")
            if form.is_valid():
                genre_obj = form.save(commit=False)
                genre_obj.created_by = request.user
                genre_obj.save()
                genre_id = genre_obj.id
                genre_name = genre_obj.name
                msg = gettext("Genre created!")

            return JsonResponse({
                "isValid": form.is_valid(),
                "msg": msg,
                "id": genre_id,
                "name": genre_name,
                "errors": json.dumps(form.errors)
            })

        return JsonResponse({
            "isValid": False,
            "msg": gettext("Invalid request type!"),
        })


def create_studio_location(profile, location, params={}):
    """
    Creates a studio location for the given profile and location object
    :param: profile: profile record
    :param: location: location record
    :params: other fields on the studio location table
    :returns: new studio location record
    """

    if profile is None or profile.type != "studio":
        return StudioLocation.object.none()

    studio = Studio.objects.filter(
        active=True, profile=profile).first()
    
    genres_list = params.get("genres", [])
    if 'genres' in params:
        del params['genres']

    if studio is None:
        studio = Studio.objects.create(
            profile=profile,
            created_by=params.get("created_by", None)
        )
        core_logger.info(
            f"New Studio created by {studio.created_by.username}"
        )

    # studio_loc = StudioLocation.objects.filter(
    #    id=params.get("id", -1)
    # ).update(**params)

    # We don't want duplications of studio and location
    studio_loc, created = StudioLocation.objects.update_or_create(
        location=location, studio=studio,
        defaults=params
    )
    if not created:
        studio_loc.updated_by = params.get("created_by", None)
        studio_loc.save()

    studio_loc.genres.set(*genres_list)

    return studio_loc


@login_required
def my_studio_locations(request):
    """
    function to list of the users studio locations
    if the profile doesn't have a studio, create a studio 
    and create subsequent locations (if sent as a POST request)
    """

    if request.method == "GET":
        locs_list = []
        item_id = request.GET.get('pk', None)

        if item_id is None:
            locs = StudioLocation.objects.filter(
                active=True,
                studio__profile=request.user.get_user_profile()
            )
        else:
            locs = StudioLocation.objects.filter(
                active=True,
                pk=item_id,
                studio__profile=request.user.get_user_profile()
            )

        for loc in locs:
            locs_list.append({
                "id": loc.id,
                "loc_pk": loc.location.id,
                "name": loc.location.name,
                "description": loc.description,
                "loc_display": loc.location.display_str(),
                "address": loc.location.address,
                "timezone": loc.location.timezone,
                "country": loc.location.country,
                "state": loc.location.state,
                "city": loc.location.city,
                "postal_code": loc.location.postal_code,
                "genres": list(loc.genres.filter(
                    active=True).values_list('id', flat=True))
            })

        return JsonResponse({
            "isValid": True,
            "locations": locs_list
        })
    elif request.method == "POST":
        genres = request.POST.getlist("genres", [])
        descr = request.POST.get("description", None)
        loc_pk = int(request.POST.get("loc_pk", -1))
        profile = request.user.get_user_profile()

        if profile is None or profile.type != "studio":
            return JsonResponse({
                "isValid": False,
                "msg": gettext("Invalid Profile or Profile is not a studio!")
            })

        msg = gettext("Form validation failed")
        loc_obj = Location.objects.filter(
            Q(pk=loc_pk) 
            | Q(postal_code__iexact=request.POST.get('postal_code'))
        ).first()
        if loc_obj:
            location_form = LocationForm(request.POST, instance=loc_obj)
        else:
            location_form = LocationForm(request.POST)

        if location_form.is_valid():
            loc_obj = location_form.save(commit=False)
            loc_obj.created_by = request.user
            loc_obj.active = True
            loc_obj.save()

            # Now, save the many-to-many data for the form.
            # location_form.save_m2m()

            create_studio_location(profile, loc_obj, {
                "created_by": request.user,
                "description": descr,
                "genres": genres,
                "id": request.POST.get('pk', -1)
            })
            msg = gettext("Studio location saved!")

        return JsonResponse({
            "isValid": location_form.is_valid(),
            "msg": msg,
            "nonFieldErrors": location_form.non_field_errors(),
            "errors": location_form.errors.get_json_data()
        })

    return JsonResponse({
        "isValid": False,
        "msg": gettext("Invalid request type")
    })


@login_required
def like_userprofile(request, pk, *args, **kwargs):
    """
    Function will like/unlike a user profile
    If a user has already liked profile, do nothing
    If a user has disliked profile, remove and add a like

    :params: pk - pk of profile to be liked
    :params: action - like/unlike action to take for the profile
    :returns: JSON - msg and whether or not action completed
    """
    is_valid = False
    action = request.GET.get("action", "like")

    try:
        profile = UserProfile.objects.get(pk=pk)

        # user_has_liked = profile.likes.filter(user=request.user)
        # user_has_disliked = profile.dislikes.filter(user=request.user)

        if action == "dislike":
            # remove like, and add dislike
            profile.likes.remove(request.user)
            profile.dislikes.add(request.user)
            msg = gettext("Profile disliked!")
        else:
            # remove dislike and add like
            profile.dislikes.remove(request.user)
            profile.likes.add(request.user)
            msg = gettext("Profile liked!")

    except UserProfile.DoesNotExist:
        msg = gettext("Profile not found!")

    return JsonResponse({
        "isValid": is_valid,
        "msg": msg
    })


@login_required
def follow_userprofile(request, pk, *args, **kwargs):
    """
    Function will follow/unfollow a user profile
    If a user has already followed profile, unfollow

    :params: pk - pk of profile to be liked
    :returns: JSON - msg and whether or not action completed
    """
    is_valid = False

    try:
        profile = UserProfile.objects.get(pk=pk)
        user_following = profile.followers.filter(user=request.user)

        if user_following.exists():
            # unfollow
            profile.followers.remove(request.user)
            msg = gettext("You have unfollowed this user!")
        else:
            # follow
            profile.followers.add(request.user)
            msg = gettext("You are now following this user!")

    except UserProfile.DoesNotExist:
        msg = gettext("Profile not found!")

    return JsonResponse({
        "isValid": is_valid,
        "msg": msg
    })


def subscribers(request):
    valid = False
    msg = ""

    if request.method == "GET":
        return JsonResponse({"isValid": valid, "msg": "Invalid request type"})
    else:
        if request.method == "POST":
            form = EmailSubscriberForm(request.POST)
            if form.is_valid():
                submition_form = form.save(commit=False)
                submition_form.save()
                msg = "Email saved successfully!"
        
        return JsonResponse({
            "isValid":form.is_valid(), "msg": msg,
            "errors":json.dumps(form.errors)})


@login_required
def studio_details(request, *args, **kwargs):
    context = {}

    try:
        profile = UserProfile.objects.get(
            user__username__iexact=kwargs.get("username"),
            active=True, type="studio"
        )
        context["profile"] = profile
        context["studio"] = Studio.objects.get(id=kwargs.get("pk"))

        return render(request, 'home/studio_details.html', context)
    except (UserProfile.DoesNotExist, Studio.DoesNotExist):
        context["error_msg"] = \
            gettext("Oops looks like the requested studio does not exist!")
        return render(request, '404.html', context)


@login_required
def profile_details(request, *args, **kwargs):
    context = {}

    try:
        profile = UserProfile.objects.get(
            user__username__iexact=kwargs.get("username"),
            active=True, type__in=["dancer", "creator"]
        )
        context["profile"] = profile
        return render(request, 'home/profile_details.html', context)
    except UserProfile.DoesNotExist:
        context["error_msg"] = \
            gettext("Oops looks like the requested profile does not exist!")
        return render(request, '404.html', context)


def get_top_dancer_genres(nums=6):
    top_dancer_genres = Genre.objects.filter(
        active=True, userprofile__active=True,
        userprofile__type="dancer"
    ).annotate(
        dancer_count=Count('userprofile__genres')
    ).order_by('-dancer_count')[0:nums]

    if not top_dancer_genres:
        top_dancer_genres = Genre.objects.filter(
            active=True
        )[0:nums]

    return top_dancer_genres


def get_top_creator_genres(nums=6):
    top_creator_genres = Genre.objects.filter(
        active=True, userprofile__active=True,
        userprofile__type="creator"
    ).annotate(
        creator_count=Count('userprofile__genres')
    ).order_by('-creator_count')[0:nums]

    if not top_creator_genres:
        top_creator_genres = Genre.objects.filter(
            active=True
        )[0:nums]

    return top_creator_genres


"""
@login_required
def notification_seen(request, notification_pk, *args, **kwargs):
    notification = Notification.objects.get(pk=notification_pk)

    notification.user_has_seen = True
    notification.save()
"""
