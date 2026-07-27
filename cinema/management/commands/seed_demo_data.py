from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cinema.models import Auditorium, MenuItem, Movie, Screening

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


# Films announced but not yet scheduled: they carry a future release date and
# no screenings, so they land in "Coming soon". Deliberately invented rather
# than real unreleased films, whose dates would be guesses - and they show off
# the generated key-art, since a film that is not out has no poster to fetch.
DEMO_UPCOMING = [
    (
        "The Longest Winter",
        "A lighthouse keeper and a stranded pilot wait out a storm that will "
        "not end.",
        180,
        128,
    ),
    (
        "Paper Moons",
        "Two estranged sisters drive across the country to sell their late "
        "father's observatory.",
        240,
        104,
    ),
    (
        "Neon Harbour",
        "A dock worker uncovers a smuggling ring hidden under the night market.",
        300,
        118,
    ),
    (
        "Silent Orbit",
        "A repair crew wakes to find their station has drifted out of contact.",
        420,
        137,
    ),
]


def create_upcoming(today):
    """Films to advertise before they open. No screenings by design."""
    for title, description, days_away, runtime in DEMO_UPCOMING:
        Movie.objects.get_or_create(
            title=title,
            defaults={
                "description": description,
                "release_date": today + timedelta(days=days_away),
                "runtime_minutes": runtime,
            },
        )


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


# (name, description, category, price yen, Wikimedia Commons file title)
#
# Files are named exactly so `fetch_menu_images` can look each one up; a
# keyword search would happily return a portrait of the man who invented
# nachos. Everything on Commons is freely licensed, so unlike film posters
# these can be real photographs.
DEMO_MENU = [
    (
        "Salted popcorn (L)",
        "The big tub. Freshly popped, lightly salted.",
        MenuItem.Category.POPCORN,
        700,
        "File:Bowl of Popcorn (Unsplash).jpg",
    ),
    (
        "Caramel popcorn (L)",
        "Sweet, sticky and worth the napkins.",
        MenuItem.Category.POPCORN,
        800,
        "File:Caramel Popcorn (32402585090).jpg",
    ),
    (
        "Nachos with cheese",
        "Warm tortilla chips under melted cheese.",
        MenuItem.Category.SNACKS,
        750,
        "File:Nachos-cheese (cropped).jpg",
    ),
    (
        "Hot dog",
        "Grilled, in a soft bun, with mustard and relish.",
        MenuItem.Category.SNACKS,
        650,
        "File:Hot dogs with relish and mustard.jpg",
    ),
    (
        "Soft pretzel",
        "Baked to order and salted.",
        MenuItem.Category.SNACKS,
        500,
        "File:Flavored soft pretzels.jpg",
    ),
    (
        "Cola (M)",
        "Over ice. Free refills at the counter.",
        MenuItem.Category.DRINKS,
        450,
        "File:Tumbler of cola with ice (cropped).jpg",
    ),
    (
        "Bottled water",
        "Still, chilled, 500ml.",
        MenuItem.Category.DRINKS,
        250,
        "File:Bottle of Water.jpg",
    ),
    (
        "Iced coffee",
        "Cold brew over ice.",
        MenuItem.Category.DRINKS,
        550,
        "File:Iced Coffee in Glass - Sunshine Coffee - Laramie Cafe (53838344552).jpg",
    ),
    (
        "Ice cream cup",
        "Vanilla, with sprinkles and a spoon.",
        MenuItem.Category.DESSERTS,
        600,
        "File:Ice cream in cup with sprinkles and spoon.jpg",
    ),
    (
        "Churros",
        "Cinnamon sugar, with a chocolate dip.",
        MenuItem.Category.DESSERTS,
        700,
        "File:Churros bought from food truck at Churchill Square 2023-07-28.jpg",
    ),
]


def create_menu():
    """Stock the concession stand. Images are fetched separately."""
    for order, (name, description, category, price, source) in enumerate(DEMO_MENU):
        MenuItem.objects.get_or_create(
            name=name,
            defaults={
                "description": description,
                "category": category,
                "price": price,
                "image_source": source,
                "sort_order": order,
            },
        )


class Command(BaseCommand):
    help = "Create demo movies and screenings if the database has none."

    def handle(self, *args, **options):
        # The concession menu does not depend on the film catalogue, so it is
        # stocked even on an install that already has movies. get_or_create
        # keeps that safe to repeat.
        create_menu()

        if Movie.objects.exists():
            self.stdout.write("Movies already exist - skipping demo movies.")
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

        create_upcoming(now.date())

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Movie.objects.count()} movies "
                f"({len(DEMO_UPCOMING)} coming soon), "
                f"{Screening.objects.count()} screenings "
                f"and {MenuItem.objects.count()} menu items."
            )
        )
