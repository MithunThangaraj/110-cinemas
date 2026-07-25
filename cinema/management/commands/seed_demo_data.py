from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cinema.models import Movie, Screening

# (title, description, release_date, runtime_minutes)
DEMO_MOVIES = [
    (
        "Dune: Part Three",
        "The Fremen rise as Paul's empire faces its long-delayed reckoning.",
        date(2027, 10, 15),
        165,
    ),
    (
        "Neon Harbour",
        "A dock worker uncovers a smuggling ring hidden under the night market.",
        date(2026, 9, 4),
        118,
    ),
    (
        "The Grand Budapest Hotel",
        "A concierge and his lobby boy chase a stolen painting across Europe.",
        date(2014, 3, 28),
        99,
    ),
    (
        "Spirited Away",
        "A girl wanders into a world of spirits to win back her parents.",
        date(2001, 7, 20),
        125,
    ),
    (
        "Paper Moons",
        "Two estranged sisters drive across the country to sell their late "
        "father's observatory.",
        date(2026, 5, 22),
        104,
    ),
    (
        "Silent Orbit",
        "A repair crew wakes to find their station has drifted out of contact.",
        date(2026, 11, 6),
        137,
    ),
    (
        "The Last Bookshop",
        "A bookseller fights to keep the oldest shop in the city from closing.",
        date(2025, 12, 12),
        92,
    ),
    (
        "Midnight Ramen",
        "Regulars at a tiny late-night counter trade the stories they cannot "
        "tell anyone else.",
        date(2026, 2, 14),
        88,
    ),
]

# (venue, days from now, hour, price)
DEMO_SCREENINGS = [
    ("Screen 1 - IMAX", 1, 18, "18.50"),
    ("Screen 2", 1, 21, "14.50"),
    ("Screen 3 - Dolby", 2, 20, "16.00"),
    ("Screen 2", 3, 15, "12.00"),
]


def create_screenings(movie, schedule, now):
    """Create one Screening per (venue, days, hour, price) entry."""
    for venue, days, hour, price in schedule:
        start_time = (now + timedelta(days=days)).replace(
            hour=hour, minute=0, second=0, microsecond=0
        )
        # Saving a Screening generates its seats via a post_save signal.
        Screening.objects.create(
            movie=movie,
            venue=venue,
            start_time=start_time,
            base_price=price,
        )


class Command(BaseCommand):
    help = "Create demo movies and screenings if the database has none."

    def handle(self, *args, **options):
        if Movie.objects.exists():
            self.stdout.write("Movies already exist - skipping demo data.")
            return

        now = timezone.now()
        for index, details in enumerate(DEMO_MOVIES):
            title, description, release_date, runtime = details
            movie = Movie.objects.create(
                title=title,
                description=description,
                release_date=release_date,
                runtime_minutes=runtime,
            )
            # Stagger how many screenings each movie gets so the listing looks
            # like a real schedule rather than the same rows repeated.
            create_screenings(movie, DEMO_SCREENINGS[: 2 + index % 3], now)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Movie.objects.count()} movies "
                f"and {Screening.objects.count()} screenings."
            )
        )
