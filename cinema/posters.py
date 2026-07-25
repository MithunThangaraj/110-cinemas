"""Look up movie poster artwork using Apple's iTunes Search API.

The API needs no key and no account, so deployment stays configuration-free.
Its film coverage is incomplete, so finding nothing is an expected outcome:
the movie simply keeps the generated key-art rendered by `_poster.html`.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request

SEARCH_URL = "https://itunes.apple.com/search"
# The size in an artwork URL is just a path segment, so a 100px thumbnail URL
# can be rewritten to ask for poster-sized (2:3) artwork instead.
THUMBNAIL_SIZE = "100x100bb.jpg"
POSTER_SIZE = "600x900bb.jpg"
TIMEOUT_SECONDS = 15
RESULT_LIMIT = 25


def _normalise(title):
    """Reduce a title to letters and digits, for tolerant comparison."""
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def _search(title):
    """Query the iTunes Search API and return its raw results."""
    query = urllib.parse.urlencode(
        {"term": title, "country": "US", "limit": RESULT_LIMIT}
    )
    with urllib.request.urlopen(
        f"{SEARCH_URL}?{query}", timeout=TIMEOUT_SECONDS
    ) as response:
        return json.load(response).get("results", [])


def find_poster_url(title, search=_search):
    """Return poster artwork for `title`, or None when there is no exact match.

    Only an exact title match counts. The API cheerfully returns loosely
    related films — searching for "Parasite" offers a Superman film — and the
    wrong poster is worse than no poster.

    `search` is injectable so callers (and tests) can avoid the network.
    """
    try:
        results = search(title)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        # A lookup failure must never break seeding or a deploy.
        return None

    wanted = _normalise(title)
    for result in results:
        if result.get("kind") != "feature-movie":
            continue
        if _normalise(result.get("trackName", "")) != wanted:
            continue
        artwork = result.get("artworkUrl100", "")
        if artwork:
            return artwork.replace(THUMBNAIL_SIZE, POSTER_SIZE)
    return None
