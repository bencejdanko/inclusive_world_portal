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
    def survey_is_complete(self) -> bool:
        """Check if user has completed the discovery survey."""
        try:
            return self.discovery_survey.is_complete
        except AttributeError:
            return False
    
    @property
    def forms_are_complete(self) -> bool:
        """Check if user has completed profile and survey forms."""
        return self.profile_is_complete and self.survey_is_complete
    
    @property
    def can_purchase_programs(self) -> bool:
        """
        Check if user (member) can purchase programs.
        Requires both completed forms AND enrollment to be open.
        """
        # Import here to avoid circular dependency
        from inclusive_world_portal.portal.models import EnrollmentSettings
        
        enrollment_settings = EnrollmentSettings.get_settings()
        return self.forms_are_complete and enrollment_settings.enrollment_open
    
    @property
    def can_register_as_volunteer(self) -> bool:
        """
        Check if user (volunteer, manager, or person_centered_manager) can register for programs without payment.
        Requires both completed forms AND enrollment to be open.
        Same logic as can_purchase_programs but for volunteers (no payment needed).
        Managers and person-centered managers are treated as higher-level volunteers.
        """
        # Import here to avoid circular dependency
        from inclusive_world_portal.portal.models import EnrollmentSettings
        
        enrollment_settings = EnrollmentSettings.get_settings()
        return self.role in [self.Role.VOLUNTEER, self.Role.MANAGER, self.Role.PERSON_CENTERED_MANAGER] and self.forms_are_complete and enrollment_settings.enrollment_open


class DiscoverySurvey(models.Model):
    """
    Stores user responses to the discovery survey used for One Page Profile generation.
    Uses JSON fields for flexibility as requirements may change.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discovery_survey"
    )
    
    # Completion tracking
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # More About You - Who is on your team
    people_closest_to_you = models.TextField(
        _("Who is on your team? Who do you turn to when you need help?"),
        blank=True,
        help_text="At home, at school, friends"
    )
    
    # Great things about you
    great_things_about_you = models.TextField(
        _("What are some great things about you that you'd like us to know about? What great things do people say about you?"),
        blank=True
    )
    
    # Things you like to do
    things_like_to_do = models.TextField(
        _("What kinds of things do you like to do at home, outside, and just for fun? Who do you like doing them with? Why?"),
        blank=True
    )
    
    # New things to learn
    things_want_to_learn = models.TextField(
        _("What new things would you like to learn to do at home, outside, and just for fun? With whom would you like to learn to do them? Why?"),
        blank=True
    )
    
    # What makes you happy and how you communicate it
    what_makes_you_happy = models.TextField(
        _("What makes you happy? How do you communicate feeling happy?"),
        blank=True
    )
    
    # What makes you sad/mad/frustrated and how you communicate it
    what_makes_you_sad = models.TextField(
        _("What makes you sad/mad/frustrated? How do you communicate that?"),
        blank=True
    )
    
    # School - What you liked
    learned_at_school_liked = models.TextField(
        _("What have you learned at school that you liked? Why did you like it?"),
        blank=True
    )
    
    # School - What you didn't like
    learned_at_school_disliked = models.TextField(
        _("What have you learned at school that you didn't like? Why didn't you like it? Could it have been presented differently?"),
        blank=True
    )
    
    # Employment
    prior_jobs = models.TextField(
        _("Have you had a job? If so, what jobs have you done?"),
        blank=True
    )
    
    # IEP - What's working
    iep_working = models.TextField(
        _("What are 3 ways your Individualized Education Program (IEP) is working for you?"),
        blank=True
    )
    
    # IEP - What's not working
    iep_not_working = models.TextField(
        _("What are 3 ways your Individualized Education Program (IEP) isn't working for you? How can Inclusive World support you there?"),
        blank=True
    )
    
    # How you like to learn (JSON field for checkboxes)
    learning_style = models.JSONField(
        default=None,
        null=True,
        blank=True,
        help_text="How do you like to learn? Check all that apply."
    )
    
    # Supportive devices
    supportive_devices = models.TextField(
        _("Are there any supportive devices you use to enable learning?"),
        blank=True
    )
    
    # Environment preferences
    working_environment_preferences = models.TextField(
        _("What are your environment preferences? Please share your environmental sensitivity."),
        blank=True
    )
    
    # Form helper
    form_helper = models.CharField(
        _("Who helped you work on this form today?"),
        max_length=255,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Discovery Questions"
        verbose_name_plural = "Discovery Questions"
    
    def __str__(self):
        return f"Discovery Questions - {self.user.username}"
    
    def get_template_context(self):
        """
        Maps survey responses to template variables for One Page Profile generation.
        Returns a dictionary with all the template variables.
        """
        user = self.user
        
        return {
            # Name
            'fname': user.name.split()[0] if user.name else user.username,
            'lname': ' '.join(user.name.split()[1:]) if user.name and len(user.name.split()) > 1 else '',
            
            # More About You
            'about_you_who_is_on_your_team': self.people_closest_to_you,
            'about_you_great_things': self.great_things_about_you,
            'about_you_things_you_like_to_do': self.things_like_to_do,
            'about_you_things_you_want_to_learn': self.things_want_to_learn,
            
            # Communication - Happy/Sad
            'about_you_happy': self.what_makes_you_happy,
            'about_you_sad': self.what_makes_you_sad,
            
            # School
            'about_you_learned_at_school_liked': self.learned_at_school_liked,
            'about_you_learned_at_school_didnt_like': self.learned_at_school_disliked,
            
            # Employment
            'about_you_jobs': self.prior_jobs,
            
            # IEP
            'about_you_iep_working': self.iep_working,
            'about_you_iep_not_working': self.iep_not_working,
            
            # Learning Style
            'about_you_how_to_learn': self._get_learning_style_summary(),
            'supportive_devices': self.supportive_devices,
            'about_your_working_environment': self.working_environment_preferences,
            
            # Helper
            'form_helper': self.form_helper,
        }
    
    def _get_learning_style_summary(self):
        """Helper to extract learning style summary from JSON."""
        if not self.learning_style or not isinstance(self.learning_style, dict):
            return ''
        
        # Try to get pre-computed summary first
        summary = self.learning_style.get('summary', '')
        if summary:
            return summary
        
        # Build summary from individual flags
        styles = []
        if self.learning_style.get('visual'):
            styles.append('Visual')
        if self.learning_style.get('auditory'):
            styles.append('Auditory')
        if self.learning_style.get('reading_writing'):
            styles.append('Reading/Writing')
        if self.learning_style.get('kinesthetic'):
            styles.append('Kinesthetic')
        
        return ', '.join(styles) if styles else ''

