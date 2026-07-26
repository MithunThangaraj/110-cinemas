"""Look up concession photographs on Wikimedia Commons.

Commons needs no API key, and everything on it is freely licensed — unlike film
posters, which is why the menu can use real photographs rather than fall back
to generated art.

Files are looked up by their exact title rather than by search: a search for
"nachos" returns a portrait of the man who invented them, and the wrong picture
on a menu is worse than no picture.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://commons.wikimedia.org/w/api.php"
# Commons rejects requests without a descriptive User-Agent.
USER_AGENT = (
    "110Cinemas/0.1 (course project; https://github.com/MithunThangaraj/110-cinemas)"
)
THUMB_WIDTH = 640
TIMEOUT_SECONDS = 20


def _strip_markup(value):
    """Commons returns small HTML fragments for credit fields."""
    text = []
    depth = 0
    for char in value:
        if char == "<":
            depth += 1
        elif char == ">":
            depth = max(depth - 1, 0)
        elif depth == 0:
            text.append(char)
    return " ".join("".join(text).split())


def _request(file_title):
    query = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": THUMB_WIDTH,
        }
    )
    request = urllib.request.Request(
        f"{API_URL}?{query}", headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.load(response)


def find_image(file_title, request=_request):
    """Return {"url", "credit"} for a Commons file, or None.

    `request` is injectable so callers (and tests) can avoid the network.
    """
    try:
        payload = request(file_title)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        # A lookup failure must never break seeding or a deploy.
        return None

    pages = (payload.get("query") or {}).get("pages") or {}
    for page in pages.values():
        images = page.get("imageinfo") or []
        if not images:
            continue
        info = images[0]
        url = info.get("thumburl") or info.get("url")
        if not url:
            continue
        metadata = info.get("extmetadata") or {}
        artist = _strip_markup(metadata.get("Artist", {}).get("value", ""))
        licence = _strip_markup(metadata.get("LicenseShortName", {}).get("value", ""))
        credit = " / ".join(
            part for part in (artist, licence, "Wikimedia Commons") if part
        )
        return {"url": url, "credit": credit}
    return None
