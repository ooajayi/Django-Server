from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from taggit.managers import TaggableManager

from .common import path_and_rename

from common.models import BaseModel


def get_event_path(instance, filename):
    return path_and_rename('events/', filename)


class ListingAdmin(admin.ModelAdmin):
    list_filter = (
        "can_apply",
        "is_approved",
        "active",
        "listing_type",
        "applicant_gender",
        "applicant_age",
        "loc_option",
        "price_type"
    )
    list_display_links = ("id", "title")
    search_fields = ["title"]
    list_display = (
        "id",
        "title",
        "loc_option",
        "start_dt",
        "expiry_dt"
    )
    autocomplete_fields = ["files"]
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")


class Listing(BaseModel):
    LISTING_TYPES = (
        ('teaching', 'Teaching'),
        ('casting', 'Casting Callout'),
        ('other', 'Other')
    )
    AGE_RANGE = (
        ('1', '0 - 9'),
        ('2', '10 - 18'),
        ('3', '19 - 29'),
        ('4', '30 - 49'),
        ('5', '50 or greater')
    )
    APPLICANT_GENDER = (
        ('any', 'Any'),
        ('female', 'Female'),
        ('male', 'Male'),
        ('other', 'Other')
    )
    LISTING_LOCATION = (
        ('onsite', 'On-Site'),
        ('inperson', 'In Person'),
        ('international', 'International'),
        ('travel', 'Travel ')
    )
    PRICE_TYPE = (
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('total', 'Per Event'),
    )

    is_approved = models.BooleanField(
        _("Is listing approved"), default=False, blank=False)
    title = models.CharField(_("title"), max_length=250)
    description = models.TextField(_("Description"), blank=True, null=True)
    listing_type = models.CharField(
        _("Listing type"), blank=True, null=True,
        max_length=10, choices=LISTING_TYPES
    )
    files = models.ManyToManyField(
        "core.Attachment", verbose_name=_("files"), blank=True)
    start_dt = models.DateTimeField(_("Start Datetime"), 
        auto_now=False, auto_now_add=False,
        blank=True, null=True)
    expiry_dt = models.DateTimeField(_("Expiry Date"), 
        auto_now=False, auto_now_add=False,
        blank=True, null=True)
    can_apply = models.BooleanField(
        _("Allow application to this listing?"), default=False,
        blank=False
    )
    applicant_age = models.CharField(
        _("Applicant age range"), blank=True, null=True,
        max_length=10, choices=AGE_RANGE
    )
    applicant_gender = models.CharField(
        _("Applicant gender"), blank=True, null=True,
        max_length=6, choices=APPLICANT_GENDER
    )
    loc_option = models.CharField(
        _("Location Option"), blank=True, null=True,
        max_length=13, choices=LISTING_LOCATION
    )
    pay = models.DecimalField(
        _("Pay"), blank=True, null=True,
        max_digits=6, decimal_places=2,
    )
    price_type = models.CharField(
        max_length=6, default="hourly", choices=PRICE_TYPE)
    tags = TaggableManager(blank=True)
    #boosted
    #paid


    class Meta:
        verbose_name = _("Listing")
        verbose_name_plural = _("Listings")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("Listing_detail", kwargs={"pk": self.pk})


class EventAdmin(admin.ModelAdmin):
    list_filter = (
        "location__state",
        "location__city",
        "location__country"
    )
    list_display_links = ("id", "title")
    search_fields = ["location__country", "location__postal_code",
                     "location__state"]
    list_display = (
        "id",
        "title",
        "start_dt",
        "end_dt",
        "state",
        "country"
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    def city(self, obj):
        return obj.location.city

    def state(self, obj):
        return obj.location.state

    def postal_code(self, obj):
        return obj.location.postal_code
    
    def country(self, obj):
        return obj.location.country


class Event(BaseModel):
    title = models.CharField(_("title"), max_length=250)
    description = models.TextField(_("Description"), blank=True, null=True)
    start_dt = models.DateTimeField(_("Start Datetime"), 
        auto_now=False, auto_now_add=False,
        blank=True, null=True)
    end_dt = models.DateTimeField(_("End Datetime"), 
        auto_now=False, auto_now_add=False,
        blank=True, null=True)
    image = models.ImageField(
        _("Event Image"), upload_to=get_event_path, max_length=150)
    location = models.ForeignKey(
        "core.Location", verbose_name=_("Location"),
        on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("Event_detail", kwargs={"pk": self.pk})


class StudioEventAdmin(admin.ModelAdmin):
    list_filter = (
        "studio",
        "freq",
        "sched_type",
        "class_level",
        "price_type"
    )
    list_display_links = ("id", "title")
    search_fields = ["studio"]
    list_display = (
        "id",
        "title",
        "studio",
        "freq",
        "start_dt",
        "end_dt"
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    def studio(self, obj):
        return obj.studio.name


class StudioEvent(BaseModel):
    EVENT_FREQ = (
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    )
    SCHED_TYPE = (
        ('class', 'Dance Class'),
        ('open', 'Open Space'),
        ('event', 'Event'),
        ('unavail', 'Un-available'),
        ('closed', 'Closed'),
    )
    PRICE_TYPE = (
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('total', 'Per Event'),
    )
    CLASS_LEVEL = (
        ('any', 'Any'),
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )

    studio = models.ForeignKey("core.Studio", on_delete=models.CASCADE)
    title = models.CharField(_("title"), max_length=250)
    description = models.TextField(_("Description"), blank=True, null=True)
    sched_type = models.CharField(
        max_length=7, default="class", choices=SCHED_TYPE)
    freq = models.CharField(
        max_length=10, default="once", choices=EVENT_FREQ)
    class_level = models.CharField(
        max_length=12, default="any", choices=CLASS_LEVEL)
    price = models.DecimalField(
        _("Price"), max_digits=6, decimal_places=2, 
        blank=True, null=True)
    price_type = models.CharField(
        max_length=6, default="hourly", choices=PRICE_TYPE)
    start_dt = models.DateTimeField(_("Start Datetime"), 
        auto_now=False, auto_now_add=False,
        blank=True, null=True)
    end_dt = models.DateTimeField(_("End Datetime"), 
        auto_now=False, auto_now_add=False,
        blank=True, null=True)
    freq_end = models.DateField(_("End Datetime"), 
        auto_now=False, auto_now_add=False,
        blank=True, null=True)
    image = models.ImageField(
        _("Event Image"), upload_to=get_event_path, max_length=150,
        blank=True, null=True)

    class Meta:
        verbose_name = _("Studio Event")
        verbose_name_plural = _("Studio Events")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("Studio Event_detail", kwargs={"pk": self.pk})


class ForumTopicAdmin(admin.ModelAdmin):
    autocomplete_fields = ["comments", "likes", "dislikes"]
    search_fields = ["topic"]
    list_filter = ["active", "is_approved"]
    list_display_links = ("id", "title")
    list_display = (
        "id",
        "title",
        "comment_count"
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    def comment_count(self, obj):
        return obj.comments.count()


class ForumTopic(BaseModel):
    is_approved = models.BooleanField(
        _("Is topic approved"), default=False, blank=False)
    archive_date = models.DateTimeField(_("Date topic archived"), 
        auto_now=False, auto_now_add=False,
        blank=True, null=True
    )
    title = models.CharField(_("Forum Topic"), max_length=500)
    body = models.TextField(_("Description"), blank=True, null=True)
    tags = TaggableManager(blank=True)
    likes = models.ManyToManyField(
        "core.User", blank=True, related_name="forumtopic_likes")
    dislikes = models.ManyToManyField(
        "core.User", blank=True, related_name="forumtopic_dislikes")
    comments = models.ManyToManyField(
        "core.Comment", verbose_name=_("Forum Comments"), 
        blank=True, related_name="forum_topic_comments")


    class Meta:
        verbose_name = _("Forum Topic")
        verbose_name_plural = _("Forum Topics")

    def __str__(self):
        return self.title
