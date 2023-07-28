try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

TIME_ZONE_CHOICES = [
    (tz, tz.replace('_', ' ')) for tz in zoneinfo.available_timezones()
]
