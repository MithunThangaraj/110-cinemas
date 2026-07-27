"""Values every template needs, without every view having to pass them."""

from django.conf import settings


def review_site(request):
    """The external film review site, linked from the nav on every page."""
    return {"review_site_url": settings.REVIEW_SITE_URL}
