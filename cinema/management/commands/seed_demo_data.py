from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cinema.models import Movie, Screening

# (title, description, release_date, runtime_minutes)
#
# Titles are spelled exactly as the iTunes Search API lists them, because
# `fetch_posters` only accepts an exact match — see cinema/posters.py.
DEMO_MOVIES = [
    (
        "Dune: Part Two",
        "Paul Atreides unites with the Fremen to wage war against the "
        "conspirators who destroyed his family.",
        date(2024, 3, 1),
        166,
    ),
    (
        "Interstellar",
        "A team of explorers travels through a wormhole in search of a new "
        "home for humanity.",
        date(2014, 11, 7),
        169,
    ),
    (
        "The Batman",
        "Two years into his war on crime, Batman follows a trail of riddles "
        "left by a killer stalking Gotham.",
        date(2022, 3, 4),
        176,
    ),
    (
        "Barbie",
        "Barbie leaves the perfection of Barbie Land for the real world, and "
        "finds neither is quite what it seems.",
        date(2023, 7, 21),
        114,
    ),
    (
        "Challengers",
        "A former tennis prodigy turned coach puts her husband and her ex "
        "against each other on court.",
        date(2024, 4, 26),
        131,
    ),
    (
        "Gladiator II",
        "Years after the death of Maximus, a man forced into the Colosseum "
        "looks for a way to strike back at Rome.",
        date(2024, 11, 22),
        148,
    ),
    (
        "Furiosa: A Mad Max Saga",
        "Snatched from the Green Place as a child, Furiosa fights her way "
        "back across the Wasteland.",
        date(2024, 5, 24),
        148,
    ),
    (
        "Wonka",
        "A young chocolatier arrives in the city with a hatful of dreams and "
        "a cartel of rivals waiting for him.",
        date(2023, 12, 15),
        116,
    ),
    (
        "Deadpool & Wolverine",
        "A reluctant Wolverine is dragged into cleaning up a mess only "
        "Deadpool could have made.",
        date(2024, 7, 26),
        128,
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
