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
    
    # Section 1: About You - Great Things
    great_things_about_you = models.TextField(
        _("What are some great things about you?"),
        blank=True,
        help_text="What people appreciate about you / What people like and admire about you"
    )
    
    # Section 2: Important to Me - Your Team
    people_closest_to_you = models.TextField(
        _("Who are the people that you are closest to?"),
        blank=True,
        help_text="Who is on your team?"
    )
    
    # Section 3: Things You Like to Do
    hobbies = models.TextField(_("Hobbies"), blank=True)
    activities = models.TextField(_("Activities"), blank=True)
    entertainment = models.TextField(_("Entertainment"), blank=True)
    favorite_food = models.TextField(_("Favorite Food"), blank=True)
    favorite_people = models.TextField(_("Favorite People"), blank=True)
    favorite_outings = models.TextField(_("Favorite Outings"), blank=True)
    routines_and_rituals = models.TextField(_("Routines and Rituals"), blank=True)
    good_day_description = models.TextField(_("Describe a Good Day"), blank=True)
    bad_day_description = models.TextField(_("Describe a Bad Day"), blank=True)
    perfect_day_description = models.TextField(
        _("Your perfect day? What would you do from the time you wake up until you go to bed?"),
        blank=True
    )
    
    # Section 4: Hopes and Dreams
    hopes_and_dreams = models.TextField(_("What are your hopes and dreams?"), blank=True)
    important_to_you = models.TextField(_("What do you think is important TO you?"), blank=True)
    important_for_you = models.TextField(_("What do you think is important FOR you?"), blank=True)
    
    # Section 5: Learning and Growth
    desired_growth_areas = models.TextField(
        _("Do you have any specific desired areas of growth?"),
        blank=True
    )
    skills_to_develop = models.TextField(_("What skills would you like to develop?"), blank=True)
    things_want_to_learn = models.TextField(_("What new things would you like to learn?"), blank=True)
    
    # Section 6: School/Education Experience
    learned_at_school_liked = models.TextField(
        _("What have you learned at school that you liked?"),
        blank=True
    )
    learned_at_school_disliked = models.TextField(
        _("What have you learned at school that you didn't like?"),
        blank=True
    )
    iep_working = models.TextField(
        _("What are 3 ways your IEP is working for you?"),
        blank=True
    )
    iep_not_working = models.TextField(
        _("What are 3 ways your IEP isn't working for you?"),
        blank=True
    )
    
    # Section 7: Communication
    how_communicate_needs = models.TextField(
        _("How do you ordinarily communicate your needs?"),
        blank=True
    )
    what_makes_you_happy = models.TextField(_("What makes you happy?"), blank=True)
    how_communicate_happy = models.TextField(_("How do you communicate feeling happy?"), blank=True)
    what_makes_you_sad = models.TextField(_("What makes you sad/mad/frustrated?"), blank=True)
    how_communicate_sad = models.TextField(_("How do you communicate that?"), blank=True)
    
    # Communication Style (stored as JSON for checkboxes)
    communication_style = models.JSONField(
        default=None,
        null=True,
        blank=True,
        help_text="Stores communication preferences: words, sign language, gestures, devices, etc."
    )
    
    # Section 8: Learning Preferences
    learning_style = models.JSONField(
        default=None,
        null=True,
        blank=True,
        help_text="How do you like to learn? Visual, auditory, kinesthetic, etc."
    )
    working_environment_preferences = models.TextField(
        _("What are your environment preferences?"),
        blank=True
    )
    virtual_learning_help = models.TextField(
        _("What accommodations can we make to help you learn effectively?"),
        blank=True
    )
    supportive_devices = models.TextField(
        _("Are there any supportive devices you use to enable learning?"),
        blank=True
    )
    
    # Section 9: Staff Preferences
    ideal_staff_characteristics = models.TextField(
        _("What would you like in a staff? Ideal Person?"),
        blank=True
    )
    disliked_staff_characteristics = models.TextField(
        _("What would you not like to have in a staff?"),
        blank=True
    )
    
    # Section 10: Employment/Volunteering
    prior_jobs = models.TextField(_("Have you had a job? If so, what jobs have you done?"), blank=True)
    jobs_interested_in = models.TextField(_("What kind of jobs are you interested in?"), blank=True)
    dream_job = models.TextField(_("What is your dream job? What type of work do you want to do?"), blank=True)
    employment_goals = models.TextField(_("What are your employment goals?"), blank=True)
    available_to_work_on = models.JSONField(
        default=None,
        null=True,
        blank=True,
        help_text="Days/times available for work"
    )
    hours_per_week_working = models.CharField(_("Hours per week available"), max_length=50, blank=True)
    
    # Section 11: Why Inclusive World
    why_interested_in_iw = models.TextField(
        _("Why are you interested in Inclusive World?"),
        blank=True
    )
    goals_and_expectations = models.TextField(
        _("What are your goals and expectations?"),
        blank=True
    )
    community_activities_interest = models.TextField(
        _("Community Activities you heard about, haven't tried, but would like to learn more about?"),
        blank=True
    )
    
    # Section 12: Support Needs
    risk_factors = models.TextField(
        _("Any Risk Factors to be aware of"),
        blank=True,
        help_text="Confidential information for staff"
    )
    day_program_recommendations = models.TextField(
        _("Day Program Recommendations"),
        blank=True,
        help_text="Summarize areas they would like support in"
    )
    
    # Section 13: Additional Information
    has_ged_or_diploma = models.BooleanField(_("Do you have a GED or High School Diploma?"), null=True, blank=True)
    training_courses_completed = models.TextField(_("List any training courses completed or certified in"), blank=True)
    how_heard_about_us = models.JSONField(
        default=None,
        null=True,
        blank=True,
        help_text="Sources: Family/Friends, Social Media, etc."
    )
    
    # Metadata
    form_helper = models.CharField(
        _("Who helped you work on this form today?"),
        max_length=255,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Discovery Survey"
        verbose_name_plural = "Discovery Surveys"
    
    def __str__(self):
        return f"Discovery Survey - {self.user.username}"
    
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
            
            # About You - Great Things
            'about_you_great_things': self.great_things_about_you,
            
            # About You - Your Team
            'about_you_who_is_on_your_team': self.people_closest_to_you,
            
            # Activities and Interests
            'about_you_things_you_like_to_do': f"{self.hobbies}\n{self.activities}\n{self.entertainment}",
            'hobbies': self.hobbies,
            'activities': self.activities,
            'entertainment': self.entertainment,
            'food': self.favorite_food,
            'favorite_people': self.favorite_people,
            'favorite_outings': self.favorite_outings,
            'routines_and_rituals': self.routines_and_rituals,
            'good_day_bad_day': f"Good Day: {self.good_day_description}\nBad Day: {self.bad_day_description}",
            
            # Perfect Day
            'perfect_day_description': self.perfect_day_description,
            
            # Hopes and Dreams
            'hopes_and_dreams': self.hopes_and_dreams,
            'important_to_you': self.important_to_you,
            'important_for_you': self.important_for_you,
            
            # Learning
            'about_you_things_you_want_to_learn': self.things_want_to_learn,
            'desired_growth_areas': self.desired_growth_areas,
            'skills_to_develop': self.skills_to_develop,
            
            # School
            'about_you_learned_at_school_liked': self.learned_at_school_liked,
            'about_you_learned_at_school_didnt_like': self.learned_at_school_disliked,
            'about_you_iep_working': self.iep_working,
            'about_you_iep_not_working': self.iep_not_working,
            
            # Communication
            'how_communicate_needs': self.how_communicate_needs,
            'about_you_happy': self.what_makes_you_happy,
            'how_communicate_happy': self.how_communicate_happy,
            'about_you_sad': self.what_makes_you_sad,
            'how_communicate_sad': self.how_communicate_sad,
            'how_do_you_communicate_that': f"Happy: {self.how_communicate_happy}\nSad: {self.how_communicate_sad}",
            
            # Why IW
            'why_are_you_interested': self.why_interested_in_iw,
            'goals_and_expectations': self.goals_and_expectations,
            'community_activities_interest': self.community_activities_interest,
            
            # Employment
            'about_you_jobs': self.prior_jobs,
            'jobs_interested_in': self.jobs_interested_in,
            'available_to_work_on': self._get_availability_summary(),
            'hours_per_week_working': self.hours_per_week_working,
            'dream_job': self.dream_job,
            'employment_goals': self.employment_goals,
            
            # Learning Style
            'about_you_how_to_learn': self._get_learning_style_summary(),
            'about_your_working_environment': self.working_environment_preferences,
            'virtual_learning_help': self.virtual_learning_help,
            'supportive_devices': self.supportive_devices,
            
            # Staff Preferences
            'ideal_staff_characteristics': self.ideal_staff_characteristics,
            'disliked_staff_characteristics': self.disliked_staff_characteristics,
            
            # Support Needs
            'day_program_recommendations': self.day_program_recommendations,
            'risk_factors': self.risk_factors,
            
            # Education/Training
            'has_ged_or_diploma': 'Yes' if self.has_ged_or_diploma else ('No' if self.has_ged_or_diploma is False else 'Not specified'),
            'training_courses_completed': self.training_courses_completed,
            
            # Communication Style (from JSON)
            'communication_uses_words': self._get_comm_style('uses_words'),
            'communication_initiate': self._get_comm_style('can_initiate_conversations'),
            'communication_nonverbal': self._get_comm_style('communicates_nonverbal'),
            'communication_articulate': self._get_comm_style('can_articulate_needs'),
            'communication_sign': self._get_comm_style('uses_sign_language'),
            'communication_device': self._get_comm_style('needs_electronic_device'),
            'communication_pictures': self._get_comm_style('uses_pictures'),
            'communication_augmented': self._get_comm_style('uses_augmented_system'),
            'communication_gestures': self._get_comm_style('uses_pointing_gesturing'),
            'communication_other_language': self._get_comm_style('other_language'),
            'communication_other': self._get_comm_style('communication_other'),
        }
    
    def _get_comm_style(self, key):
        """Helper to extract communication style values from JSON."""
        if not self.communication_style or not isinstance(self.communication_style, dict):
            return ''
        
        value = self.communication_style.get(key, '')
        
        # Convert boolean to Yes/No
        if isinstance(value, bool):
            return 'Yes' if value else 'No'
        
        return value if value else ''
    
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
            styles.append('visual')
        if self.learning_style.get('auditory'):
            styles.append('auditory')
        if self.learning_style.get('kinesthetic'):
            styles.append('kinesthetic')
        if self.learning_style.get('reading'):
            styles.append('reading/writing')
        if self.learning_style.get('social'):
            styles.append('social')
        if self.learning_style.get('solitary'):
            styles.append('solitary')
        
        other = self.learning_style.get('other', '')
        result = ', '.join(styles)
        if other:
            result += f', {other}' if result else other
        
        return result if result else ''
    
    def _get_availability_summary(self):
        """Helper to extract availability summary from JSON."""
        if not self.available_to_work_on:
            return ''
        
        if isinstance(self.available_to_work_on, dict):
            # Try to get pre-computed summary first
            summary = self.available_to_work_on.get('summary', '')
            if summary:
                return summary
            
            # Build summary from individual flags
            times = []
            if self.available_to_work_on.get('weekdays'):
                times.append('Weekdays')
            if self.available_to_work_on.get('weekends'):
                times.append('Weekends')
            if self.available_to_work_on.get('mornings'):
                times.append('Mornings')
            if self.available_to_work_on.get('afternoons'):
                times.append('Afternoons')
            if self.available_to_work_on.get('evenings'):
                times.append('Evenings')
            
            other = self.available_to_work_on.get('other', '')
            result = ', '.join(times)
            if other:
                result += f', {other}' if result else other
            
            return result if result else ''
        elif isinstance(self.available_to_work_on, list):
            return ', '.join(self.available_to_work_on)
        else:
            return str(self.available_to_work_on)
