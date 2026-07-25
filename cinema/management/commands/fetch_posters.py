"""Fill in movie posters from the iTunes Search API."""

from django.core.management.base import BaseCommand

from cinema.models import Movie
from cinema.posters import find_poster_url


class Command(BaseCommand):
    help = "Fetch missing movie posters from the iTunes Search API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Look up posters again for movies that already have one.",
        )

    def handle(self, *args, **options):
        movies = Movie.objects.all()
        if not options["force"]:
            movies = movies.filter(poster_image="")

        found = 0
        for movie in movies:
            url = find_poster_url(movie.title)
            if not url:
                # Expected for anything the store does not carry; the movie
                # keeps its generated key-art.
                self.stdout.write(f"No poster found for {movie.title}.")
                continue
            movie.poster_image = url
            movie.save(update_fields=["poster_image"])
            found += 1

        self.stdout.write(self.style.SUCCESS(f"Set {found} poster(s)."))
