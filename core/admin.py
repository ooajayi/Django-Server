from django.contrib import admin
from core.models.user import (
    User, UserAdmin, UserProfile, UserProfileAdmin, Studio, StudioAdmin,
    StudioLocation, StudioLocationAdmin, EmailSubscribers)
from core.models.classifieds import (
    Event, EventAdmin, ForumTopic, ForumTopicAdmin, Listing, ListingAdmin,
    StudioEvent, StudioEventAdmin)
from core.models.common import (
    Attachment, AttachmentAdmin, Comment, CommentAdmin, Genre, Location,
    LocationAdmin)
from core.models.util import (
    Advertisement, AdvertisementAdmin, Contact, DCC, FAQ, GoogleTag, Option)

# Register your models here.

admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Studio, StudioAdmin)
admin.site.register(StudioLocation, StudioLocationAdmin)
admin.site.register(EmailSubscribers)
admin.site.register(Advertisement, AdvertisementAdmin)
admin.site.register(Contact)
admin.site.register(Comment, CommentAdmin)
admin.site.register(DCC)
admin.site.register(Event, EventAdmin)
admin.site.register(FAQ)
admin.site.register(ForumTopic, ForumTopicAdmin)
admin.site.register(Genre)
admin.site.register(GoogleTag)
admin.site.register(Location, LocationAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Option)
admin.site.register(StudioEvent, StudioEventAdmin)
