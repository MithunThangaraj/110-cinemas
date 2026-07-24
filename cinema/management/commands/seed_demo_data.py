from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cinema.models import Movie, Screening

# (title, description, release_date, runtime_minutes)
DEMO_MOVIES = [
    (
        "Dune: Part Three",
        "The Fremen rise as Paul's empire faces its reckoning.",
        date(2027, 10, 15),
        165,
    ),
    (
        "The Grand Budapest Hotel",
        "A concierge and his lobby boy chase a stolen painting.",
        date(2014, 3, 28),
        99,
    ),
    (
        "Spirited Away",
        "A girl wanders into a world of spirits to free her parents.",
        date(2001, 7, 20),
        125,
    ),
]

# (venue, days from now, hour, price)
DEMO_SCREENINGS = [
    ("Auditorium 1", 1, 18, "14.50"),
    ("Auditorium 2", 2, 20, "12.00"),
]


class Command(BaseCommand):
    help = "Create demo movies and screenings if the database has none."

    def handle(self, *args, **options):
        if Movie.objects.exists():
            self.stdout.write("Movies already exist - skipping demo data.")
            return

        now = timezone.now()
        for title, description, release_date, runtime in DEMO_MOVIES:
            movie = Movie.objects.create(
                title=title,
                description=description,
                release_date=release_date,
                runtime_minutes=runtime,
            )
            for venue, days, hour, price in DEMO_SCREENINGS:
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

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Movie.objects.count()} movies "
                f"and {Screening.objects.count()} screenings."
            )
        )
