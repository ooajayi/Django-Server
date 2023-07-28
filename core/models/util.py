from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from common.models import BaseModel
from .common import path_and_rename


def get_advert_path(instance, filename):
    return path_and_rename('advertisements/', filename)


class GoogleTag(BaseModel):
    TAG_PLACEMENT = (
        ('head', "Head"),
        ('top_body', "Inside Body Top"),
        ('bottom_body', "Inside Body Bottom"),
        ('footer', "Footer"),
    )

    name = models.CharField(_("Google Tag name"), max_length=120)
    placement =  models.CharField(
        _("Tag Placement"), max_length=11, 
        default="head", choices=TAG_PLACEMENT)
    script = models.TextField("Script to insert", blank=True, null=True)

    def __str__(self):
        return '%s' %self.name

    class Meta:
        verbose_name = _("Google Tag")
        verbose_name_plural = _("Google Tags")


class AdvertisementAdmin(admin.ModelAdmin):
    list_filter = (
        "placement", "shape"
    )
    search_fields = ["name"]
    list_display = (
        "id",
        "name",
        "placement",
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")


class Advertisement(BaseModel):
    AD_PLACEMENT = (
        ('head', "Head"),
        ('top_body', "Inside Body Top"),
        ('bottom_body', "Inside Body Bottom"),
        ('footer', "Footer"),
        ('sidebar', "Sidebar"),
    )

    SHAPE = (
        ('square', "Square"),
        ('circle', "Circle"),
        ('horizontal', "Horizontal"),
        ('vertical', "Vertical"),
    )
    
    AD_TYPE = (
        ('script', "Script"),
        ('image', "Image"),
    )

    name = models.CharField(_("Ad name"), max_length=120)
    placement =  models.CharField(
        _("Tag Placement"), max_length=11, 
        default="head", choices=AD_PLACEMENT)
    shape =  models.CharField(
        _("Tag Shape"), max_length=11, 
        default="landscape", choices=SHAPE)
    ad_type =  models.CharField(
        _("Ad Type"), max_length=6, 
        default="image", choices=AD_TYPE)
    script = models.TextField("Script to insert", blank=True, null=True)
    image = models.ImageField(
        _("Ad Image"), upload_to=get_advert_path, max_length=150)
    image_target = models.CharField(
        _("External link for image ad"), max_length=150, blank=True, null=True
    )

    def __str__(self):
        return '%s' %self.name

    class Meta:
        verbose_name = _("Advertisement")
        verbose_name_plural = _("Advertisements")


class Option(BaseModel):
    VALUE_TYPES = (
        ("text", "Text"),
        ("int", "Integer"),
        ("num", "Number"),
        ("date", "Date"),
        ("time", "Time"),
    )

    name = models.CharField("Unique Name", max_length=100, unique=True)
    label = models.CharField("Option Front End Display Name", max_length=150)
    value = models.CharField("Value", max_length=500)
    value_type = models.CharField(
        "Value Type", max_length=6,
        choices=VALUE_TYPES, default="text")

    class Meta:
        ordering = ["name"]
        verbose_name = "Option"
        verbose_name_plural = "Options"

    def __str__(self):
        return '%s' %self.label


class FAQ(BaseModel):
    title = models.CharField(_("FAQ title"), max_length=200)
    body = models.TextField(_("FAQ Body"), blank=True, null=True)
    disp_order = models.IntegerField(_("Display Order"), default=1)

    class Meta:
        ordering = ["title", "disp_order"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return '%s' %self.title


class DCC(models.Model):
    name = models.CharField(
        _("Site name"), max_length=100, blank=True, null=True)
    title = models.CharField(
        _("Site title"), max_length=150, blank=True, null=True)
    def_logo = models.ImageField(
        _("Default Logo"), upload_to="logos/", max_length=150)
    alt_logo = models.ImageField(
        _("Alternate Logo"), upload_to="logos/", max_length=150)
    privacy_policy = models.FileField(
        _("Privacy Policy"), blank=True, null=True, upload_to="legal/"
    )
    tandc = models.FileField(
        _("Terms and Conditions"), blank=True, null=True,
        upload_to="legal/"
    )
    keywords = models.CharField(
        _("Keywords"), max_length=150, blank=True, null=True)
    facebook = models.CharField(
        _("Facebook profile"), max_length=128, blank=True, null=True)
    instagram = models.CharField(
        _("Instagram"), max_length=128, blank=True, null=True)
    twitter = models.CharField(
        _("Twitter"), max_length=128, blank=True, null=True)
    tiktok = models.CharField(
        _("Tik Tok"), max_length=128, blank=True, null=True)
    youtube = models.CharField(
        _("Youtube"), max_length=128, blank=True, null=True)

    class Meta:
        verbose_name = _("DCC")
        verbose_name_plural = _("DCCs")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("DCC_detail", kwargs={"pk": self.pk})


class Contact(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('responded', 'Replied'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    )

    name = models.CharField("Name", max_length=150)
    email = models.CharField("Email", max_length=100)
    status = models.CharField(
        max_length=15, default="new", choices=STATUS_CHOICES)
    reason = models.CharField(
        _("Reason for Contact"), max_length=256, blank=True, null=True)
    msg = models.TextField(
        _("Contact Body"), blank=True, null=True)
    resolution = models.TextField(
        _("Resolution"), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Contact Form"
        verbose_name_plural = "Contact Forms"

    def __str__(self):
        return '%s - Contact Inquiry' %(self.name)
