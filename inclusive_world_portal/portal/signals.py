from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
import django.db.models as models

from .models import Enrollment, Program, UserProfile, UserRole, UserRoleType

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_and_default_role(sender, instance, created, **kwargs):
    if not created:
        return
    # Create profile with whatever you have (fill later via forms)
    UserProfile.objects.get_or_create(
        user=instance,
        defaults={"first_name": instance.first_name or "", "last_name": instance.last_name or "", "email": instance.email},
    )
    # Assign default "member" role if none exists
    UserRole.objects.get_or_create(user=instance, role=UserRoleType.MEMBER)

@receiver(post_save, sender=Enrollment)
def bump_enrollment_on_create(sender, instance, created, **kwargs):
    if created and instance.status == "approved":  # or whatever states should count
        Program.objects.filter(pk=instance.program_id).update(enrolled=models.F("enrolled") + 1)

@receiver(post_delete, sender=Enrollment)
def lower_enrollment_on_delete(sender, instance, **kwargs):
    Program.objects.filter(pk=instance.program_id, enrolled__gt=0).update(enrolled=models.F("enrolled") - 1)
