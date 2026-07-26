from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cinema.models import Auditorium, Movie, Screening

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

# (name, screen format, surcharge in yen). Surcharges follow Japanese
# multiplex pricing: premium formats cost more, 4DX most of all.
DEMO_AUDITORIUMS = [
    ("IMAX GT", Auditorium.Format.IMAX_GT, 1000),
    ("Dolby Cinema", Auditorium.Format.DOLBY, 1000),
    ("4DX Screen 3", Auditorium.Format.FOUR_DX, 1200),
    ("Screen 5", Auditorium.Format.STANDARD, 0),
    ("Screen 6", Auditorium.Format.STANDARD, 0),
]

# The standard adult ticket; the auditorium and the seat add to it.
BASE_PRICE_YEN = 2000

# (auditorium name, days from now, hour)
DEMO_SCREENINGS = [
    ("IMAX GT", 1, 18),
    ("Screen 5", 1, 21),
    ("Dolby Cinema", 2, 20),
    ("4DX Screen 3", 2, 17),
    ("Screen 6", 3, 15),
]


def create_auditoriums():
    """Create the screens, one per format plus a second standard room."""
    auditoriums = {}
    for name, screen_format, surcharge in DEMO_AUDITORIUMS:
        auditoriums[name], _ = Auditorium.objects.get_or_create(
            name=name,
            defaults={"screen_format": screen_format, "surcharge": surcharge},
        )
    return auditoriums


def create_screenings(movie, schedule, now, auditoriums):
    """Create one Screening per (auditorium, days, hour) entry."""
    for name, days, hour in schedule:
        start_time = (now + timedelta(days=days)).replace(
            hour=hour, minute=0, second=0, microsecond=0
        )
        # Saving a Screening generates its seats via a post_save signal, laid
        # out according to the auditorium's format.
        Screening.objects.create(
            movie=movie,
            auditorium=auditoriums[name],
            start_time=start_time,
            base_price=BASE_PRICE_YEN,
        )


class Command(BaseCommand):
    help = "Create demo movies and screenings if the database has none."

    def handle(self, *args, **options):
        if Movie.objects.exists():
            self.stdout.write("Movies already exist - skipping demo data.")
            return

        auditoriums = create_auditoriums()
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
            create_screenings(movie, DEMO_SCREENINGS[: 2 + index % 3], now, auditoriums)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Movie.objects.count()} movies "
                f"and {Screening.objects.count()} screenings."
            )
        )
