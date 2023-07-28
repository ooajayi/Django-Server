from datetime import datetime

from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

from common.models import BaseModel
from common.func_utils import get_obj_loc_str

from PIL import Image

from .common import get_path_for_uploaded_profile, Attachment


class UserAdmin(admin.ModelAdmin):
    list_filter = (
        "is_staff",
        "is_superuser",
    )
    search_fields = ["username", "email", "last_name", "first_name"]
    list_display = (
        "id",
        "username",
        "first_name",
        "last_name",
    )
    # readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")


class User(AbstractUser):
    class Meta:
        ordering = ["first_name", "last_name"]

    def get_user_fullname(self):
        name = self.username
        if self.first_name:
            name = self.first_name
            if self.last_name:
                name += ' ' + self.last_name

        return name
    
    def get_primary_email(self):
        email = self.email

        for emailaddress in self.emailaddress_set.all():
            if emailaddress.primary and emailaddress.verified:
                email = emailaddress
                break
            elif emailaddress.verified:
                email = emailaddress
                break

        return email

    def has_verified_email(self):
        return self.emailaddress_set.filter(verified=True).exists()

    def get_user_profile(self):
        try:
            profile = UserProfile.objects.get(user=self)
        except:
            profile = UserProfile.objects.none()

        return profile

    def __str__(self):
        return '%s - %s %s' %(self.username, self.first_name, self.last_name)


class UserProfileAdmin(admin.ModelAdmin):
    list_filter = (
        "type",
        "active",
        "is_verified",
        # "subscription",
    )
    # search_fields = ["email", "last_name", "first_name"]
    list_display = (
        "id",
        "type",
        "email",
        "display_name",
        "date_joined",
        # "subscription",
    )

    def email(self, obj):
        return obj.user.email


class UserProfile(models.Model):
    PROFILE_TYPES = (
        ('dancer', 'Dancer'),
        ('creator', 'Creator'),
        ('studio', 'Studio'),
        ('stud_admin', 'Studio Administrator'),
        ('sys_admin', 'System Administrator'),
    )

    LOCATION_SHARE_PREF = (
        ('all', 'Show all'),
        ('country', 'Only display my country'),
        ('province', 'Include province and country'),
        ('city', 'Show city, province and country'),
        ('none', 'Hide all'),
    )
    TIME_ZONE_CHOICES = [
        (tz, tz.replace('_', ' ')) for tz in zoneinfo.available_timezones()
    ]


    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='user')
    type = models.CharField(
        max_length=10, 
        default="dancer", 
        choices=PROFILE_TYPES)
    cover_photo = models.ImageField(
        _("Cover photo"), blank=True, null=True, 
        upload_to=get_path_for_uploaded_profile
    )
    profile_photo = models.ImageField(
        _("Profile photo"), blank=True, null=True,
        upload_to=get_path_for_uploaded_profile
    )
    avatar = models.ImageField(
        "Avatar", blank=True, null=True,
        upload_to=get_path_for_uploaded_profile,
    )
    resume = models.FileField(
        "Resume", blank=True, null=True,
        upload_to=get_path_for_uploaded_profile,
    )
    active = models.BooleanField("Is profile active?", default=True)
    bio = models.TextField(blank=True, null=True)
    dob = models.DateField("Date of Birth", blank=True, null=True)
    alt_name = models.CharField(max_length=50, blank=True, null=True)
    full_name = models.CharField(max_length=128, blank=True, null=True)
    display_name = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField("Phone", max_length=24, blank=True, null=True)
    organization = models.CharField(max_length=100, blank=True, null=True)
    alt_phone = models.CharField(
        _("Alternate Phone"), max_length=24, 
        blank=True, null=True)
    timezone = models.CharField(
        max_length=100, 
        default="America/Edmonton", 
        choices=TIME_ZONE_CHOICES, blank=True)
    is_verified = models.BooleanField(
        _("Verified User"), default=False
    )
    receive_promo_emails = models.BooleanField(
        _("Receive promo email notifications"), default=False
    )
    receive_other_emails = models.BooleanField(
        _("Receive other email notifications"), default=False
    )
    loc_share_pref = models.CharField(
        _("Location sharing preference"), default="all", 
        choices=LOCATION_SHARE_PREF,
        max_length=10,
    )
    tc_agreed = models.BooleanField(
        _("Accepted Terms and Conditions?"), default=True)
    address = models.CharField(max_length=150, blank=True, null=True)
    city = models.CharField(max_length=150, blank=True, null=True)
    province = models.CharField(max_length=150, blank=True, null=True)
    country = models.CharField(max_length=150, blank=True, null=True)
    postal_code = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(max_length=150, blank=True, null=True)
    facebook = models.CharField(max_length=150, blank=True, null=True)
    instagram = models.CharField(max_length=150, blank=True, null=True)
    twitter = models.CharField(max_length=150, blank=True, null=True)
    tiktok = models.CharField(
        _("Tik Tok"), max_length=150, blank=True, null=True)
    youtube = models.CharField(max_length=150, blank=True, null=True)
    linkedin = models.CharField(max_length=150, blank=True, null=True)
    genres = models.ManyToManyField("core.Genre", blank=True)
    interests = models.ManyToManyField("core.Interest", blank=True)

    likes = models.ManyToManyField(
        User, blank=True, related_name='profile_likes')
    dislikes = models.ManyToManyField(
        User, blank=True, related_name='profile_dislikes')
    followers = models.ManyToManyField(
        User, blank=True, related_name='profile_followers')

    photos = models.ManyToManyField(
        Attachment, blank=True, related_name='profile_photos')
    videos = models.ManyToManyField(
        Attachment, blank=True, related_name='profile_videos')

    date_joined = models.DateTimeField('Date Joined', auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_age(self):
        if self.dob:
            return int((datetime.now().date() - self.dob).days / 365.25)

        return None

    def display_loc_str(self):
        return get_obj_loc_str(self)

    def get_studio(self):
        if self.type == "studio":
            return Studio.objects.filter(
                profile=self, active=True).first()
        else:
            return Studio.objects.none()
        
    def studio_locations(self):
        if self.type == "studio":
            return StudioLocation.objects.filter(
                studio__profile=self
            )
        else:
            return StudioLocation.objects.none()

    """
    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        profile = UserProfile.objects.filter(user=instance).first()
        if created and not profile:
            UserProfile.objects.create(
                user=instance,
                full_name=instance.first_name + ' ' + instance.last_name
            )
        else:
            try:
                UserProfile.objects.get(user=instance).save()
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(
                    user=instance,
                    full_name=instance.first_name + ' ' + instance.last_name
                )
    """

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        # save the profile first
        super().save(*args, **kwargs)

        # resize the avatar
        if self.avatar:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                # create a thumbnail
                img.thumbnail(output_size)
                # overwrite the larger image
                img.save(self.avatar.path)

        # resize the profile photo
        if self.profile_photo:
            img = Image.open(self.profile_photo.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                # create a thumbnail
                img.thumbnail(output_size)
                # overwrite the larger image
                img.save(self.profile_photo.path)


class StudioAdmin(admin.ModelAdmin):
    # list_filter = (
    #    "status",
    # )
    list_display = (
        "id",
        "name",
        "contact"
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    def name(self, obj):
        return obj.profile.display_name or obj.name

    def contact(self, obj):
        return obj.profile.user.email


class Studio(BaseModel):
    profile = models.ForeignKey(
        UserProfile, verbose_name=_("UserProfile"),
        on_delete=models.CASCADE)
    name = models.CharField(_("Studio Name"), max_length=120)
    email = models.CharField(
        _("Email"), max_length=124, blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=24, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_photo = models.ImageField(
        _("Profile photo"), blank=True, null=True,
        upload_to=get_path_for_uploaded_profile
    )
    locations = models.ManyToManyField(
        "core.Location", verbose_name=_("Locations"),
        blank=True, through="StudioLocation",
        through_fields=('studio', 'location'))
    admins = models.ManyToManyField(
        "core.User", verbose_name=_("Admin Users"),
        blank=True)
    genres = models.ManyToManyField("core.Genre", blank=True)

    address = models.CharField(max_length=150, blank=True, null=True)
    city = models.CharField(max_length=150, blank=True, null=True)
    province = models.CharField(max_length=150, blank=True, null=True)
    country = models.CharField(max_length=150, blank=True, null=True)
    postal_code = models.CharField(max_length=50, blank=True, null=True)

    website = models.URLField(max_length=150, blank=True, null=True)
    facebook = models.CharField(max_length=150, blank=True, null=True)
    instagram = models.CharField(max_length=150, blank=True, null=True)
    twitter = models.CharField(max_length=150, blank=True, null=True)
    tiktok = models.CharField(
        _("Tik Tok"), max_length=150, blank=True, null=True)
    youtube = models.CharField(max_length=150, blank=True, null=True)

    likes = models.ManyToManyField(
        User, blank=True, related_name='studios_liked')
    dislikes = models.ManyToManyField(
        User, blank=True, related_name='studios_disliked')
    followers = models.ManyToManyField(
        User, blank=True, related_name='studios_followed')

    files = models.ManyToManyField(
        Attachment, blank=True, related_name='studio_files')

    class Meta:
        verbose_name = _("Studio")
        verbose_name_plural = _("Studios")

    
    def display_loc_str(self):
        return get_obj_loc_str(self)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Studio_detail", kwargs={"pk": self.pk})


class StudioLocationAdmin(admin.ModelAdmin):
    # list_filter = (
    #    "country", "state", "genres"
    # )
    list_display = (
        "id",
        "address",
        "postal_code",
        "state",
        "country"
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    def address(self, obj):
        return obj.location.address

    def country(self, obj):
        return obj.location.country
    
    def postal_code(self, obj):
        return obj.location.postal_code

    def state(self, obj):
        return obj.location.state


class StudioLocation(BaseModel):
    studio = models.ForeignKey("core.Studio", on_delete=models.CASCADE)
    location = models.ForeignKey("core.Location", on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    genres = models.ManyToManyField(
        "core.Genre",
        verbose_name=_("Studio Location Genres"), blank=True,
        related_name="genres", related_query_name="genre"
    )

    class Meta:
        unique_together = ("studio", "location")
        verbose_name = _("Studio Location")
        verbose_name_plural = _("Studio Locations")

    def __str__(self):
        studio_name = self.studio.profile.display_name
        loc_disp = self.location.postal_code

        return f"{studio_name} >> {loc_disp}"


class EmailSubscribers(models.Model):
    email = models.EmailField(null=False, blank=True, max_length=200, unique=True)
    status = models.CharField(max_length=64, null=False, blank=True)
    created_at = models.DateTimeField(null=False, blank=True)
    updated_at = models.DateTimeField(null=False, blank=True)

    class Meta:
        verbose_name = _("Email Subscriber")
        verbose_name_plural = _("Email Subscribers")

    def __str__(self):
        return self.email


"""
class SubscriptionAdmin(admin.ModelAdmin):
    list_filter = (
        "level",
        "status",
    )
    list_display = (
        "id",
        "profile",
        "level",
        "status",
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")


class Subscription(models.Model):
    SUBSCRIPTION_LEVEL = (
        ('basic', 'Basic'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    )
    SUBSCRIPTION_STATUS = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    profile = restructure = models.ForeignKey(Profile, on_delete=models.CASCADE)
    level = models.CharField(
        "Subscription Level", max_length=15, default="basic", 
        choices=SUBSCRIPTION_LEVEL)
    status = models.CharField(
        "Subscription Status", max_length=15, default="active", 
        choices=SUBSCRIPTION_STATUS)
    reason = models.TextField("Subscription Message", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["email"]
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    def __str__(self):
        return '%s' %(self.email)
"""
