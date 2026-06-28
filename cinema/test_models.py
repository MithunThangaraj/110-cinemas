import uuid
from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from .models import Movie, Reservation, Screening, Seat
from .services import cancel_reservation, reserve_seat


@pytest.fixture
def movie():
    return Movie.objects.create(
        title="Dune: Part Three",
        description="The sandworms return.",
        release_date=date(2027, 10, 15),
        runtime_minutes=165,
    )


@pytest.fixture
def future_screening(movie):
    return Screening.objects.create(
        movie=movie,
        venue="Auditorium 1",
        start_time=timezone.now() + timedelta(days=7),
        base_price="14.50",
    )


@pytest.mark.django_db
class TestMovie:
    def test_create_movie(self):
        movie = Movie.objects.create(
            title="Test Movie",
            release_date=date(2026, 1, 1),
            runtime_minutes=120,
        )
        assert movie.title == "Test Movie"
        assert str(movie) == "Test Movie"

    def test_movie_ordering(self):
        Movie.objects.create(
            title="Older", release_date=date(2024, 1, 1), runtime_minutes=90
        )
        Movie.objects.create(
            title="Newer", release_date=date(2025, 1, 1), runtime_minutes=90
        )
        movies = Movie.objects.all()
        assert movies[0].title == "Newer"

    def test_movie_requires_title(self):
        with pytest.raises(ValidationError):
            movie = Movie(release_date=date(2026, 1, 1), runtime_minutes=120)
            movie.full_clean()


@pytest.mark.django_db
class TestScreening:
    def test_create_screening(self, movie):
        start = timezone.now() + timedelta(days=1)
        screening = Screening.objects.create(
            movie=movie,
            venue="Auditorium 1",
            start_time=start,
            base_price="14.50",
        )
        assert screening.movie == movie
        assert str(movie) in str(screening)

    def test_screening_past_start_time_raises(self, movie):
        past = timezone.now() - timedelta(days=1)
        with pytest.raises(ValidationError):
            Screening.objects.create(
                movie=movie,
                venue="Auditorium 1",
                start_time=past,
                base_price="14.50",
            )

    def test_screening_generates_seats(self, future_screening):
        seats = Seat.objects.filter(screening=future_screening)
        assert seats.count() == 96


@pytest.mark.django_db
class TestSeat:
    def test_seat_unique_together(self, future_screening):
        Seat.objects.create(screening=future_screening, row="Z", number=99)
        with pytest.raises(IntegrityError):
            Seat.objects.create(screening=future_screening, row="Z", number=99)

    def test_seat_available_by_default(self, future_screening):
        seat = future_screening.seats.first()
        assert seat.is_available is True

    def test_seat_not_available_when_reserved(self, future_screening):
        seat = future_screening.seats.first()
        Reservation.objects.create(seat=seat)
        assert seat.is_available is False


@pytest.mark.django_db
class TestReservation:
    def test_create_reservation(self, future_screening):
        seat = future_screening.seats.first()
        reservation = Reservation.objects.create(seat=seat)
        assert reservation.status == "confirmed"
        assert isinstance(reservation.booking_id, uuid.UUID)

    def test_unique_active_reservation(self, future_screening):
        seat = future_screening.seats.first()
        Reservation.objects.create(seat=seat)
        with pytest.raises(IntegrityError):
            Reservation.objects.create(seat=seat)

    def test_cancelled_reservation_allows_new(self, future_screening):
        seat = future_screening.seats.first()
        r1 = Reservation.objects.create(seat=seat)
        r1.status = "cancelled"
        r1.save(update_fields=["status"])
        r2 = Reservation.objects.create(seat=seat)
        assert r2.status == "confirmed"


@pytest.mark.django_db
class TestServices:
    def test_reserve_seat(self, future_screening):
        seat = future_screening.seats.first()
        reservation = reserve_seat(seat.id)
        assert reservation.status == "confirmed"
        assert reservation.seat == seat

    def test_reserve_already_reserved_seat(self, future_screening):
        seat = future_screening.seats.first()
        reserve_seat(seat.id)
        with pytest.raises(ValidationError):
            reserve_seat(seat.id)

    def test_cancel_reservation(self, future_screening):
        seat = future_screening.seats.first()
        reservation = reserve_seat(seat.id)
        cancel_reservation(reservation.id)
        reservation.refresh_from_db()
        assert reservation.status == "cancelled"

    def test_seat_available_after_cancel(self, future_screening):
        seat = future_screening.seats.first()
        reservation = reserve_seat(seat.id)
        cancel_reservation(reservation.id)
        assert seat.is_available is True

    def test_available_seats_query_excludes_reserved(self, future_screening):
        all_seats = list(future_screening.seats.all())
        first_seat = all_seats[0]
        second_seat = all_seats[1]
        reserve_seat(first_seat.id)
        available = [
            s for s in Seat.objects.filter(screening=future_screening)
            if s.is_available
        ]
        assert first_seat not in available
        assert second_seat in available
