import pytest
from django.core.management import call_command
from django.utils import timezone

from .models import Auditorium, Movie, Screening, Seat


@pytest.mark.django_db
class TestSeedDemoData:
    def test_seeds_movies_screenings_and_seats(self):
        call_command("seed_demo_data")
        assert Movie.objects.count() > 0
        assert Screening.objects.count() > 0
        # Saving a screening generates its seats via the post_save signal,
        # laid out to suit the auditorium it is in.
        expected = sum(s.auditorium.seat_count for s in Screening.objects.all())
        assert Seat.objects.count() == expected

    def test_seeds_one_auditorium_per_format(self):
        call_command("seed_demo_data")
        formats = set(Auditorium.objects.values_list("screen_format", flat=True))
        assert formats == {"standard", "imax_gt", "dolby", "4dx"}

    def test_imax_is_the_biggest_room(self):
        call_command("seed_demo_data")
        rooms = sorted(Auditorium.objects.all(), key=lambda a: a.seat_count)
        assert rooms[-1].screen_format == Auditorium.Format.IMAX_GT
        assert rooms[0].screen_format == Auditorium.Format.FOUR_DX

    def test_every_room_has_wheelchair_spaces(self):
        call_command("seed_demo_data")
        for screening in Screening.objects.all():
            spaces = screening.seats.filter(kind=Seat.Kind.WHEELCHAIR).count()
            assert spaces > 0, screening.auditorium.name

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
