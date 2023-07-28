import json
import operator

from functools import reduce

from django.core.paginator import EmptyPage, Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.translation import gettext
from django.views import generic

from core.models.common import Comment
from core.models.classifieds import ForumTopic, Listing
from core.forms.classified import ForumTopicForm


@login_required
def create_forum_topic(request):
    valid = False
    msg = ""

    if request.method == "GET":
        return JsonResponse({"isValid": valid, "msg": "Invalid request type"})
    else:
        if request.method == "POST":
            form = ForumTopicForm(request.POST)
            if form.is_valid():
                forum_topic = form.save(commit=False)
                forum_topic.save()
                msg = gettext("Question created and will be approved shortly!")

        return JsonResponse({
            "isValid": form.is_valid(),
            "msg": msg,
            "errors": json.dumps(form.errors)
        })


class ListingsView(LoginRequiredMixin, generic.ListView):
    template_name = 'home/listings.html'
    model = Listing
    context_object_name = "listings"

    def get_queryset(self):
        return Listing.objects.filter(
            Q(expiry_dt__gte=timezone.now()) | Q(expiry_dt__isnull=True),
            active=True, is_approved=True
        ).distinct().prefetch_related("tags").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["price_types"] = Listing.PRICE_TYPE
        context["applicant_ages"] = Listing.AGE_RANGE
        context["applicant_genders"] = Listing.APPLICANT_GENDER
        context["loc_options"] = Listing.LISTING_LOCATION
        context["listing_types"] = Listing.LISTING_TYPES
        context["tags"] = Listing.tags.all()

        return context


class ListingDetailsView(LoginRequiredMixin, generic.DetailView):
    template_name = 'home/listing_details.html'
    model = Listing
    context_object_name = "listing"

    def get_queryset(self):
        return Listing.objects.filter(
            Q(expiry_dt__gte=timezone.now()) | Q(expiry_dt__isnull=True),
            pk=self.kwargs.get('pk'), active=True, is_approved=True
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['access_records'] = 

        return context


class ListingsHtmxView(LoginRequiredMixin, generic.TemplateView):
    template_name = "components/htmx/listings.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        search_str: str = self.request.GET.get("srch", "")
        page: int = self.request.GET.get("page", 1)
        init_load: int = self.request.GET.get("initLoad", 1)
        page_len: int = self.request.GET.get("page_len", 15)
        gender = self.request.GET.getlist("gender", [])
        listing_type = self.request.GET.getlist("listing_type", [])
        loc_option = self.request.GET.getlist("loc_option", [])
        price_type = self.request.GET.getlist("price_type", [])
        age_range = self.request.GET.getlist("age_range", [])

        context["listings"] = get_listings_to_display(
            search_str, page=page, pg_len=page_len,
            gender=gender, listing_type=listing_type, loc_option=loc_option,
            price_type=price_type, age=age_range
        )
        context["page"] = page
        context["init_load"] = init_load

        context["gender"] = gender
        context["listing_type"] = listing_type
        context["loc_option"] = loc_option
        context["price_type"] = price_type
        context["age_range"] = age_range
        context["srch"] = search_str

        return context


class ForumTopicsView(LoginRequiredMixin, generic.ListView):
    template_name = 'home/topics.html'
    model = ForumTopic
    context_object_name = "topics"

    def get_queryset(self):
        return ForumTopic.objects.filter(
            Q(archive_date__gte=timezone.now()) | Q(archive_date__isnull=True),
            active=True, is_approved=True
        ).distinct().prefetch_related("comments").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class ForumTopicDetailsView(LoginRequiredMixin, generic.DetailView):
    template_name = 'home/topic_details.html'
    model = ForumTopic
    context_object_name = "topic"

    def get_queryset(self):
        return ForumTopic.objects.filter(
            Q(archive_date__gte=timezone.now())
            | Q(archive_date__isnull=True),
            pk=self.kwargs.get('pk'), active=True, is_approved=True
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['access_records'] = 

        return context


class ForumTopicsHtmxView(LoginRequiredMixin, generic.TemplateView):
    template_name = "components/htmx/topics.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        search_str: str = self.request.GET.get("srch", "")
        page: int = self.request.GET.get("page", 1)
        page_len: int = self.request.GET.get("page_len", 1)

        context["topics"] = get_topics_to_display(
            search_str, page=page, pg_len=page_len
        )
        context["page"] = page
        context["srch"] = search_str

        return context


def get_latest_listings():
    return Listing.objects.filter(
            Q(expiry_dt__gte=timezone.now()) | Q(expiry_dt__isnull=True),
            active=True, is_approved=True
        ).order_by("-created_at")


def get_latest_forum_topics():
    return ForumTopic.objects.filter(
            active=True, is_approved=True
        ).prefetch_related('comments').order_by("-created_at")


def get_listings_to_display(srch_val="", page=1, pg_len=20, gender=[],
                            listing_type=[], loc_option=[], price_type=[],
                            age=[]):
    values = srch_val.split()
    query = None

    if values:
        query = reduce(operator.and_,
                       [Q(title__icontains=v) |
                        Q(tag__name__icontains=v) |
                        Q(description__icontains=v) 
                        for v in values])

    listing_objs = Listing.objects.filter(
        Q(expiry_dt__gte=timezone.now()) | Q(expiry_dt__isnull=True),
        active=True, is_approved=True
    )

    objs = listing_objs.filter(query) if query is not None else listing_objs

    if gender:
        objs = objs.filter(applicant_gender__in=gender)

    if listing_type:
        objs = objs.filter(listing_type__in=listing_type)

    if loc_option:
        objs = objs.filter(loc_option__in=loc_option)

    if age:
        objs = objs.filter(applicant_age__in=age)

    if price_type:
        objs = objs.filter(price_type__in=price_type)

    results = objs.distinct().prefetch_related("tags").order_by("-created_at")
    listing_paginator = Paginator(results, pg_len)

    try:
        requests_list = listing_paginator.page(page)
    except EmptyPage:
        requests_list = listing_paginator.page(listing_paginator.num_pages)

    return requests_list


def get_topics_to_display(srch_val="", page=1, pg_len=20):
    values = srch_val.split()
    query = None

    if values:
        query = reduce(operator.and_,
                       [Q(title__icontains=v) for v in values])

    topic_objs = ForumTopic.objects.filter(
        Q(archive_date__gte=timezone.now()) | Q(archive_date__isnull=True),
        active=True, is_approved=True
    )

    objs = topic_objs.filter(query) if query is not None else topic_objs

    results = objs.distinct().prefetch_related("comments").order_by("-created_at")
    topic_paginator = Paginator(results, pg_len)

    try:
        topics_list = topic_paginator.page(page)
    except EmptyPage:
        topics_list = topic_paginator.page(topic_paginator.num_pages)

    return topics_list
