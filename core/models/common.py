import os
import uuid

from django.contrib import admin
from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

from common.models import BaseModel
from common.func_utils import get_obj_loc_str


def path_and_rename(prefix, filename):
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid.uuid4().hex, ext)

    return os.path.join(prefix, filename)

def get_path_for_uploaded_file(instance, filename):
    return path_and_rename('dcc/', filename)

def get_path_for_uploaded_profile(instance, filename):
    return path_and_rename(f'profile/{instance.id}/', filename)

def get_attachment_path(instance, filename):
    return path_and_rename('attachments/', filename)

"""
def image_transform(name, content):
    content.file.seek(0)
    with Image.open(content.file) as thumb:
        thumb.thumbnail(DEFAULT_SIZE, Image.ANTIALIAS,)

        ImageFile.MAXBLOCK = max(ImageFile.MAXBLOCK,
                                 thumb.size[0] * thumb.size[1])
        new_content = BytesIO()
        quality = -1
        if thumb.format in ('GIF', 'PNG'):
            img_format = 'PNG'
        else:
            img_format = 'JPEG'
            quality = 70
        thumb.save(new_content, format=img_format,
                   quality=quality, **thumb.info)
        new_content = ContentFile(new_content.getvalue())

        name = image_get_name(name, img_format)

    return name, new_content
"""


class AttachmentAdmin(admin.ModelAdmin):
    list_filter = (
        "file_type",
    )
    list_display_links = ("id", "label")
    search_fields = ["label"]
    list_display = (
        "id",
        "label",
        "file_type",
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")


class Attachment(BaseModel):
    ATTACHMENT_TYPES = (
        ('unset', 'Not Set'),
        ('img', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
        ('pdf', 'PDF'),
        ('word', 'Word'),
    )

    file_type = models.CharField(
        max_length=9, default="unset",
        choices=ATTACHMENT_TYPES, blank=True)
    label = models.CharField(
        _("File Label"), max_length=200, blank=True, null=True
    )
    file = models.FileField(
        _("File"), upload_to=get_attachment_path, blank=True, null=True
    )
    thumbnail = models.ImageField(
        _("File Thumbnail"),
        blank=True,
        null=True,
        upload_to=f"{get_attachment_path}/thubmnails/",
    )

    def create_thumbnail(self):
        image_field = self.file

        # if no image is attached to record delete thumbnail and return
        if not image_field:  # pragma: no cover
            self.thumbnail.delete(save=False)
            return

        import io

        from django.core.files.uploadedfile import InMemoryUploadedFile
        from PIL import Image

        # if there's an existing thumbnail, delete that and continue
        # reason for this was to delete the thumbnail file from storage if
        # no longer needed
        if self.thumbnail:  # pragma: no cover
            self.thumbnail.delete(save=False)

        # content_type = image_field.file.content_type
        image_field_name = image_field.name.split("/")[-1]
        thumbnail_name, ext = os.path.splitext(image_field_name)
        thumbnail_name = thumbnail_name + "_thumb" + ext
        thumbnail_size = (400, 340)

        thumb_format = ext[1:]
        if thumb_format.lower() in ("gif", "png"):
            thumb_format = "PNG"
        else:
            thumb_format = "JPEG"  # pragma: no cover

        content_type = f"image/{ thumb_format.lower() }"

        with Image.open(image_field.file) as image:
            image.thumbnail(thumbnail_size, Image.ANTIALIAS)
            thumb_file = io.BytesIO()
            image.save(thumb_file, thumb_format)

        self.thumbnail.save(
            thumbnail_name,
            InMemoryUploadedFile(
                thumb_file,
                None,
                thumbnail_name,
                content_type,
                thumbnail_size,
                None,
            ),
            save=False,
        )

    """
    def save(self, *args, **kwargs):
        if self.file:
            root, ext = os.path.splitext(self.file.name)
            if ext.lower() in self.imgs_file_exts:
                (
                    self.file.name,
                    self.file.file,
                ) = self.file.content = image_transform(
                    self.file.name, self.file.file
                )
                self.create_thumbnail()

        force_update = False

        # If the instance already has been saved, it has an id and we set
        # force_update to True
        if self.id:  # pragma: no cover
            force_update = True

        # Force an UPDATE SQL query if we're editing the image to avoid
        # integrity exception
        super(Attachment, self).save(force_update=force_update)
    """

    def extension(self):  # pragma: no cover
        name, ext = os.path.splitext(self.file.name)
        return ext

    def save(self, *args, **kwargs):
        img_exts = ["png", "jpg", "jpeg", "svg", "tiff"]
        vid_exts = ["mp4", "mpg", "mov", "mpeg", "wmv", "flv", "avi", "webm"]
        root, ext = os.path.splitext(self.file.name)

        if self.label is None or self.label == "":
            self.label = root

        if ext.lower() in img_exts:
            self.file_type = "img"
            self.create_thumbnail()

        if ext.lower() in vid_exts:
            self.file_type = "video"

        force_update = False

        # If instance is already exists, update label if none
        if self.id:
            force_update = True

        # Force update to avoid integrity exception
        super(Attachment, self).save(force_update=force_update)

    def delete(self, *args, **kwargs):  # pragma: no cover
        if self.file:
            self.file.delete(save=False)

        if self.thumbnail:
            self.thumbnail.delete(save=False)

        super(Attachment, self).delete()

    def __str__(self):
        return '%s' %self.label

    class Meta:
        ordering = ["label"]


class Genre(BaseModel):
    slug = models.SlugField(_("Genre Slug"), unique=True, max_length=100)
    name = models.CharField(_("Genre name"), max_length=150)

    class Meta:
        verbose_name = _("Genre")
        verbose_name_plural = _("Genre")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Genre_detail", kwargs={"pk": self.pk})


class Interest(BaseModel):
    slug = models.SlugField(_("Interest Slug"), unique=True, max_length=100)
    name = models.CharField(_("Interest name"), max_length=150)

    class Meta:
        verbose_name = _("Interest")
        verbose_name_plural = _("Interests")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Interest_detail", kwargs={"pk": self.pk})


class LocationAdmin(admin.ModelAdmin):
    list_filter = (
        "country",
        "state",
        "city"
    )
    list_display_links = ("id", "address")
    search_fields = ["country", "city", "postal_code", "state"]
    list_display = (
        "id",
        "address",
        "state",
        "country",
        "postal_code"
    )
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")


class Location(BaseModel):
    TIME_ZONE_CHOICES = [
        (tz, tz.replace('_', ' ')) for tz in zoneinfo.available_timezones()
    ]
    
    name = models.CharField(_("Name"), max_length=100, blank=True, null=True)
    address = models.CharField(_("Address"), max_length=150, blank=True, null=True)
    suite_no = models.CharField(_("Suite No"), max_length=50, blank=True, null=True)
    city = models.CharField(_("City"), max_length=50, blank=True, null=True)
    state = models.CharField(_("State"), max_length=50, blank=True, null=True)
    country = models.CharField(_("Country"), max_length=100, blank=True, null=True)
    postal_code = models.CharField(
        _("Postal Code"), max_length=50, unique=True)
    timezone = models.CharField(
        max_length=100, 
        default="America/Edmonton", 
        choices=TIME_ZONE_CHOICES, blank=True)

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    def _str__(self):
        return self.postal_code
        
    def display_loc_str(self):
        return get_obj_loc_str(self)

    def display_str(self):
        return (
            f"{self.suite_no or ''} {self.address or ''}, {self.city or ''}"
            f"{self.state or ''}\n"
            f"{self.country or ''}. {self.postal_code or ''}"
            )

    def get_absolute_url(self):
        return reverse("Location_detail", kwargs={"pk": self.pk})


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'created_at', 'is_flagged', 'is_approved', 'active'
    )
    list_filter = ('is_approved', 'is_flagged', 'active')
    search_fields = ('user__username', 'user__email', 'body')
    actions = ['approve_comments']

    def name(self, obj):
        return obj.made_by.username

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)


class Comment(BaseModel):
    made_by = models.ForeignKey(
        "core.User", verbose_name=_("User who made comment"),
        on_delete=models.CASCADE, related_name="comments_made")
    is_approved = models.BooleanField(
        _("Is comment approved"), default=False, blank=False)
    likes = models.ManyToManyField(
        "core.User", verbose_name=_("Users who like comment"),
        related_name='comments_liked')
    dislikes = models.ManyToManyField(
        "core.User", verbose_name=_("Users who dislike comment"),
        related_name='comments_disliked')
    body = models.TextField(_("Body"), blank=True, null=True)
    is_flagged = models.BooleanField(
        _("Is comment flagged"), default=False, blank=False)
    flagged_by = models.ForeignKey(
        "core.User", verbose_name=_("User who flagged comment"),
        on_delete=models.SET_NULL, blank=True, null=True,
        related_name="comments_flagged")
    flag_reason = models.TextField(_("Reason for flagging"), blank=True, null=True)


"""
class Notification(BaseModel):
    NOTIFICATION_TYPES = (
        (1, 'Like'),
        (2, 'Follower'),
        (3, 'Comment')
    )
    notification_type = models.IntegerField(
        _("Notification Type"), default=1, 
        choices=NOTIFICATION_TYPES,)
    to_user = models.ForeignKey(
        "core.User", related_name="notification_to", 
        on_delete=models.CASCADE, null=True
    )
    from_user = models.ForeignKey(
        "core.User", related_name="notification_from", 
        on_delete=models.CASCADE, null=True
    )
    record_pk = models.BigIntegerField(
        _("Primary key of related object"), default=0,
        blank=False, null=False
    )
    comment = models.ForeignKey(
        'Comment', on_delete=models.CASCADE, related_name='+', 
        blank=True, null=True
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    was_seen = models.BooleanField(default=False)
    time_seen = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
"""
