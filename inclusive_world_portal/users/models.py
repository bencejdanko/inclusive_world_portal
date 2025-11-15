from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.db.models import (
    BooleanField,
    CharField,
    DateTimeField,
    EmailField,
    ImageField,
    IntegerField,
    JSONField,
    OneToOneField,
    TextField,
    CASCADE,
)
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Default custom user model for inclusive-world-portal.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    class Role(models.TextChoices):
        MEMBER = "member", _("Member")
        VOLUNTEER = "volunteer", _("Volunteer")
        PERSON_CENTERED_MANAGER = "person_centered_manager", _("Person Centered Manager")
        MANAGER = "manager", _("Manager")

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        SUSPENDED = "suspended", _("Suspended")
        PENDING_VERIFICATION = "pending_verification", _("Pending Verification")

    # Basic Info
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    
    # Role
    role = CharField(
        _("Role"),
        max_length=50,
        choices=Role.choices,
        default=Role.MEMBER,
        help_text=_("User's role in the organization")
    )
    
    # Status
    status = CharField(
        _("Status"),
        max_length=50,
        choices=Status.choices,
        default=Status.PENDING_VERIFICATION,
        help_text=_("User's account status")
    )
    
    # Profile Information
    phone_no = CharField(_("Phone Number"), max_length=64, blank=True)
    bio = TextField(_("Bio"), blank=True)
    age = IntegerField(_("Age"), null=True, blank=True)
    grade = CharField(_("Grade"), max_length=64, blank=True)
    profile_picture = ImageField(_("Profile Picture"), upload_to="profile_pictures/", blank=True, null=True)
    support_needs = TextField(_("Support Needs"), blank=True, help_text=_("Special accommodations or support requirements"))
    
    # Parent/Guardian Information
    parent_guardian_name = CharField(_("Parent/Guardian Name"), max_length=255, blank=True)
    parent_guardian_phone = CharField(_("Parent/Guardian Phone"), max_length=64, blank=True)
    parent_guardian_email = EmailField(_("Parent/Guardian Email"), blank=True)
    
    # Emergency Contact Information
    emergency_contact_first_name = CharField(_("Emergency Contact First Name"), max_length=255, blank=True)
    emergency_contact_last_name = CharField(_("Emergency Contact Last Name"), max_length=255, blank=True)
    emergency_contact_relationship = CharField(_("Emergency Contact Relationship"), max_length=255, blank=True)
    emergency_contact_phone = CharField(_("Emergency Contact Phone"), max_length=64, blank=True)
    emergency_contact_secondary_phone = CharField(_("Emergency Contact Secondary Phone"), max_length=64, blank=True)
    emergency_contact_email = EmailField(_("Emergency Contact Email"), blank=True)
    
    phone_confirmed_at = DateTimeField(_("Phone Confirmed At"), null=True, blank=True)

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})
    
    @property
    def profile_is_complete(self) -> bool:
        """Check if user has filled out required profile information."""
        required_fields = [
            self.name,
            self.email,
            self.phone_no,
            self.age,
            self.parent_guardian_name or self.emergency_contact_first_name,  # At least one contact
        ]
        return all(field for field in required_fields)
    
    
    @property
    def meets_enrollment_requirements(self) -> bool:
        """
        Check if user meets enrollment requirements for their role.
        Uses the extensible RoleEnrollmentRequirement system.
        """
        from inclusive_world_portal.portal.models import RoleEnrollmentRequirement
        
        try:
            requirement = RoleEnrollmentRequirement.objects.get(role=self.role, is_active=True)
            meets_requirements, _ = requirement.check_user_meets_requirements(self)
            return meets_requirements
        except RoleEnrollmentRequirement.DoesNotExist:
            # No requirement configured - allow registration
            return True
    
    @property
    def enrollment_requirements_status(self) -> tuple:
        """
        Get detailed status of enrollment requirements.
        Returns (meets_requirements: bool, missing_items: list)
        """
        from inclusive_world_portal.portal.models import RoleEnrollmentRequirement
        
        try:
            requirement = RoleEnrollmentRequirement.objects.get(role=self.role, is_active=True)
            return requirement.check_user_meets_requirements(self)
        except RoleEnrollmentRequirement.DoesNotExist:
            # No requirement configured - allow registration
            return True, []
    
    @property
    def can_purchase_programs(self) -> bool:
        """
        Check if user (member) can purchase programs.
        Requires both enrollment requirements AND enrollment to be open.
        """
        # Import here to avoid circular dependency
        from inclusive_world_portal.portal.models import EnrollmentSettings
        
        enrollment_settings = EnrollmentSettings.get_settings()
        return self.meets_enrollment_requirements and enrollment_settings.enrollment_open
    
    @property
    def can_register_as_volunteer(self) -> bool:
        """
        Check if user (volunteer, manager, or person_centered_manager) can register for programs without payment.
        Requires both enrollment requirements AND enrollment to be open.
        Managers and person-centered managers are treated as higher-level volunteers.
        """
        # Import here to avoid circular dependency
        from inclusive_world_portal.portal.models import EnrollmentSettings
        
        enrollment_settings = EnrollmentSettings.get_settings()
        return self.role in [self.Role.VOLUNTEER, self.Role.MANAGER, self.Role.PERSON_CENTERED_MANAGER] and self.meets_enrollment_requirements and enrollment_settings.enrollment_open


