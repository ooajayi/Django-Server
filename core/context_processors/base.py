from django.db.models import Q
from django.utils import timezone

from core.models import DCC, Genre, GoogleTag, Option, Advertisement
from core.models.classifieds import StudioEvent

from core.views.core import get_top_creator_genres, get_top_dancer_genres
from core.views.forumtopic import get_latest_forum_topics, get_latest_listings
from core.views.studio import get_top_studio_genres


def defaults(request):
    '''
    A context processor to add the "default variables" used in the base for all views
    '''
    ctry = None
    province = None
    if request.user.is_authenticated:
        prof_obj = request.user.get_user_profile()

        if prof_obj:
            ctry = prof_obj.country
            province = prof_obj.province

    studio_events = StudioEvent.objects.filter(
        Q (studio__country__iexact=ctry, studio__province__iexact=province)
        | Q(studio__country__isnull=True, studio__province__isnull=True),
        Q (start_dt__gte=timezone.now(), end_dt__lte=timezone.now())
        | Q(start_dt__isnull=True) | Q(end_dt__isnull=True),
        active=True
    )

    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            studio_events = StudioEvent.objects.filter(active=True)

    return  {
        'dcc': DCC.objects.filter().first(),
        'genres': Genre.objects.filter(active=True),
        'tags': GoogleTag.objects.filter(active=True),
        'show_socials': Option.objects.filter(
            active=True, name="show_socials"
        ).values('label', 'value', 'value_type').first(),
        'force_signup': Option.objects.filter(
            active=True, name="force_signup"
        ).values('label', 'name', 'value', 'value_type').first(),
        'sidebar_listings': get_latest_listings()[:5],
        'sidebar_image_ads': Advertisement.objects.filter(
            active=True, image__isnull=False, placement='sidebar'
        ),
        'header_script_ads': Advertisement.objects.filter(
            active=True, image__isnull=True, placement='head'
        ),
        'footer_script_ads': Advertisement.objects.filter(
            active=True, image__isnull=True, placement='head'
        ),
        'top_body_ads': Advertisement.objects.filter(
            active=True, placement='top_body', image__isnull=True
        ),
        'top_body_banners': Advertisement.objects.filter(
            active=True, placement='top_body', image__isnull=False
        ),
        'bottom_body_ads': Advertisement.objects.filter(
            active=True, placement='bottom_body', image__isnull=True
        ),
        'bottom_body_banners': Advertisement.objects.filter(
            active=True, placement='bottom_body', image__isnull=False
        ),
        'top_studio_events': studio_events[:7],
        'sidebar_forum_topics': get_latest_forum_topics()[:5],
        'top_studio_genres': get_top_studio_genres(6),
        'top_creator_genres': get_top_creator_genres(6),
        'top_dancer_genres': get_top_dancer_genres(6)
    }
