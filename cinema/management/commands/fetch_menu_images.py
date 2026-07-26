"""Fill in concession photographs from Wikimedia Commons."""

from django.core.management.base import BaseCommand

from cinema.commons import find_image
from cinema.models import MenuItem


class Command(BaseCommand):
    help = "Fetch missing menu item images from Wikimedia Commons."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Look up images again for items that already have one.",
        )

    def handle(self, *args, **options):
        items = MenuItem.objects.exclude(image_source="")
        if not options["force"]:
            items = items.filter(image_url="")

        found = 0
        for item in items:
            image = find_image(item.image_source)
            if not image:
                self.stdout.write(f"No image found for {item.name}.")
                continue
            item.image_url = image["url"]
            item.image_credit = image["credit"]
            item.save(update_fields=["image_url", "image_credit"])
            found += 1

        self.stdout.write(self.style.SUCCESS(f"Set {found} menu image(s)."))
