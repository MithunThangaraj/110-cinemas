from datetime import date, timedelta

import pytest
from django.test import Client
from django.utils import timezone

from .models import Auditorium, Movie, Screening


@pytest.fixture
def django_client_factory():
    """Build extra clients, each with its own session.

    Used to check that one visitor cannot act on another visitor's booking.
    """
    return Client


@pytest.fixture
def movie():
    return Movie.objects.create(
        title="Dune: Part Three",
        description="The sandworms return.",
        release_date=date(2027, 10, 15),
        runtime_minutes=165,
    )


@pytest.fixture
def auditorium():
    """A standard screen: 10 rows x 18 seats."""
    return Auditorium.objects.create(
        name="Screen 5", screen_format=Auditorium.Format.STANDARD, surcharge=0
    )


@pytest.fixture
def imax_auditorium():
    return Auditorium.objects.create(
        name="IMAX GT", screen_format=Auditorium.Format.IMAX_GT, surcharge=1000
    )


@pytest.fixture
def future_screening(movie, auditorium):
    return Screening.objects.create(
        movie=movie,
        auditorium=auditorium,
        start_time=timezone.now() + timedelta(days=7),
        base_price=2000,
    )
