from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Screening, generate_seats


@receiver(post_save, sender=Screening)
def create_screening_seats(sender, instance, created, **kwargs):
    if created:
        generate_seats(instance)
