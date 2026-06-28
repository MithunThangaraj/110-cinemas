from django.apps import AppConfig


class CinemaConfig(AppConfig):
    name = "cinema"
    verbose_name = "Cinema"

    def ready(self):
        import cinema.signals  # noqa: F401
