"""Tests for the poster lookup. The network is never touched: `find_poster_url`
takes its search function as an argument.
"""

import urllib.error

import pytest

from .posters import find_poster_url

ARTWORK = (
    "https://is1-ssl.mzstatic.com/image/thumb/Video/abc/pr_source.lsr/100x100bb.jpg"
)
POSTER = (
    "https://is1-ssl.mzstatic.com/image/thumb/Video/abc/pr_source.lsr/600x900bb.jpg"
)


def result(name, kind="feature-movie", artwork=ARTWORK):
    return {"trackName": name, "kind": kind, "artworkUrl100": artwork}


class TestFindPosterUrl:
    def test_returns_poster_sized_artwork_for_an_exact_match(self):
        url = find_poster_url("Dune", search=lambda title: [result("Dune")])
        assert url == POSTER

    def test_ignores_loosely_related_films(self):
        # Searching the real API for "Parasite" offers a Superman film.
        url = find_poster_url(
            "Parasite", search=lambda title: [result("Superman: Man of Tomorrow")]
        )
        assert url is None

    def test_match_ignores_punctuation_and_case(self):
        url = find_poster_url(
            "dune part two", search=lambda title: [result("Dune: Part Two")]
        )
        assert url == POSTER

    def test_ignores_non_movie_results(self):
        url = find_poster_url(
            "Dune", search=lambda title: [result("Dune", kind="tv-episode")]
        )
        assert url is None

    def test_skips_results_without_artwork(self):
        url = find_poster_url(
            "Dune",
            search=lambda title: [result("Dune", artwork=""), result("Dune")],
        )
        assert url == POSTER

    def test_no_results_is_not_an_error(self):
        assert find_poster_url("Nothing Here", search=lambda title: []) is None

    @pytest.mark.parametrize(
        "error",
        [urllib.error.URLError("down"), TimeoutError(), OSError(), ValueError()],
    )
    def test_network_failures_return_none(self, error):
        def failing_search(title):
            raise error

        assert find_poster_url("Dune", search=failing_search) is None


@pytest.mark.django_db
class TestFetchPostersCommand:
    def test_sets_poster_for_movies_without_one(self, monkeypatch, movie):
        from django.core.management import call_command

        monkeypatch.setattr(
            "cinema.management.commands.fetch_posters.find_poster_url",
            lambda title: POSTER,
        )
        call_command("fetch_posters")
        movie.refresh_from_db()
        assert movie.poster_image == POSTER

    def test_leaves_poster_blank_when_nothing_is_found(self, monkeypatch, movie):
        from django.core.management import call_command

        monkeypatch.setattr(
            "cinema.management.commands.fetch_posters.find_poster_url",
            lambda title: None,
        )
        call_command("fetch_posters")
        movie.refresh_from_db()
        assert movie.poster_image == ""

    def test_does_not_overwrite_an_existing_poster(self, monkeypatch, movie):
        from django.core.management import call_command

        movie.poster_image = "https://example.com/mine.jpg"
        movie.save(update_fields=["poster_image"])
        monkeypatch.setattr(
            "cinema.management.commands.fetch_posters.find_poster_url",
            lambda title: POSTER,
        )
        call_command("fetch_posters")
        movie.refresh_from_db()
        assert movie.poster_image == "https://example.com/mine.jpg"

    def test_force_refetches_existing_posters(self, monkeypatch, movie):
        from django.core.management import call_command

        movie.poster_image = "https://example.com/old.jpg"
        movie.save(update_fields=["poster_image"])
        monkeypatch.setattr(
            "cinema.management.commands.fetch_posters.find_poster_url",
            lambda title: POSTER,
        )
        call_command("fetch_posters", "--force")
        movie.refresh_from_db()
        assert movie.poster_image == POSTER
