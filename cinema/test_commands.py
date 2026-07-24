import pytest
from django.core.management import call_command
from django.utils import timezone

from .models import Movie, Screening, Seat


@pytest.mark.django_db
class TestSeedDemoData:
    def test_seeds_movies_screenings_and_seats(self):
        call_command("seed_demo_data")
        assert Movie.objects.count() > 0
        assert Screening.objects.count() > 0
        # Saving a screening generates its seats via the post_save signal.
        assert Seat.objects.count() == Screening.objects.count() * 96

    def test_seeded_screenings_are_in_the_future(self):
        call_command("seed_demo_data")
        now = timezone.now()
        assert all(s.start_time > now for s in Screening.objects.all())

    def test_is_idempotent(self):
        call_command("seed_demo_data")
        movies = Movie.objects.count()
        screenings = Screening.objects.count()

        call_command("seed_demo_data")

        assert Movie.objects.count() == movies
        assert Screening.objects.count() == screenings

    def test_skips_when_movies_already_exist(self, movie):
        call_command("seed_demo_data")
        assert Movie.objects.count() == 1
