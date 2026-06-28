from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, CandidateProfile, EmployerProfile


@receiver(post_save, sender=User)
def create_profile_for_user(sender, instance, created, **kwargs):
    """Auto-create the matching profile when a user is created."""
    if not created:
        return
    if instance.role == User.Role.CANDIDATE:
        CandidateProfile.objects.get_or_create(user=instance)
    elif instance.role == User.Role.EMPLOYER:
        EmployerProfile.objects.get_or_create(user=instance)
