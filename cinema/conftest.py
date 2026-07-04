from datetime import date, timedelta

import pytest
from django.utils import timezone

from .models import Movie, Screening


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
