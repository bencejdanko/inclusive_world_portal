import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone

# -------------------------
# Choice enums (from your SQL enums)
# -------------------------

class UserStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    PENDING = "pending_verification", "Pending verification"
    SUSPENDED = "suspended", "Suspended"

class UserRoleType(models.TextChoices):
    MEMBER = "member", "Member"
    VOLUNTEER = "volunteer", "Volunteer"
    MANAGER = "manager", "Manager"
    PCM = "person_centered_manager", "Person-Centered Manager"
    UNASSIGNED = "unassigned", "Unassigned"

class EnrollmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    WAITLISTED = "waitlisted", "Waitlisted"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"

class OPDState(models.TextChoices):
    DRAFT = "draft", "Draft"
    REVIEW = "review", "Review"
    FINAL = "final", "Final"

class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Present"
    TARDY = "tardy", "Tardy"
    INFORMED = "informed", "Informed"
    UNINFORMED = "uninformed", "Uninformed"

# -------------------------
# Programs & Enrollment
# -------------------------

class Program(models.Model):
    program_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    capacity = models.PositiveIntegerField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    image = models.ImageField(upload_to='program_images/', blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    enrollment_status = models.CharField(max_length=64, blank=True)  # e.g., "open"/"closed"
    enrolled = models.PositiveIntegerField(default=0)                 # kept as counter like SQL
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["archived", "enrollment_status", "start_date"]),
        ]

    @property
    def available_spots(self) -> int:
        if self.capacity is None:
            return None
        return max(self.capacity - self.enrolled, 0)

    def __str__(self) -> str:
        """Return a friendly representation used in admin and form labels."""
        return self.name

class Enrollment(models.Model):
    enrollment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=16, choices=EnrollmentStatus.choices)
    preference_order = models.IntegerField(null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assignments_made",
        null=True, blank=True,
    )
    assignment_notes = models.TextField(blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (("user", "program"),)  # pragmatic: avoid dup enrollments
        indexes = [
            models.Index(fields=["program", "status"]),
        ]

class AttendanceRecord(models.Model):
    attendance_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="attendance_records")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_records")
    attendance_date = models.DateField()
    attendance_status = models.CharField(max_length=16, choices=AttendanceStatus.choices)
    hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("program", "user", "attendance_date"),)

class ProgramVolunteerLead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="volunteer_leads")
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lead_roles")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["program"]),
            models.Index(fields=["volunteer"]),
        ]

class BuddyAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="buddy_assignments")
    member_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buddy_member_assignments")
    volunteer_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buddy_volunteer_assignments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("program", "member_user"),)
        indexes = [
            models.Index(fields=["program"]),
            models.Index(fields=["member_user"]),
            models.Index(fields=["volunteer_user"]),
        ]

# -------------------------
# Surveys
# -------------------------
# Using django-survey-and-report package directly
# No custom models needed - the package provides Survey, Question, Response, etc.

# -------------------------
# Payments
# -------------------------

class Payment(models.Model):
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=12)
    status = models.CharField(max_length=64)
    payment_method = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# -------------------------
# Documents
# -------------------------

class DocumentState(models.TextChoices):
    DRAFT = "draft", "Draft"
    REVIEW = "review", "Review"
    FINAL = "final", "Final"

class Document(models.Model):
    """
    User documents created with the Quill editor.
    Each user can have multiple documents (e.g., One Page Description, notes, etc.)
    Managers can create documents for other users.
    
    Publishing:
    - When published, a PDF is generated and saved to S3/MinIO storage
    - The PDF can be viewed in a framed view (not public, requires login)
    - Only one PDF per document - regenerated each time you publish
    """
    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="The user this document belongs to"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents_created",
        help_text="Manager/PCM who created this document (null if user created it themselves)"
    )
    title = models.CharField(max_length=255, default="Untitled Document")
    content = models.TextField(blank=True, help_text="HTML content from Quill editor")
    state = models.CharField(
        max_length=16,
        choices=DocumentState.choices,
        default=DocumentState.DRAFT,
        help_text="Current state of the document"
    )
    source_survey = models.ForeignKey(
        'survey.Survey',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_documents",
        help_text="Survey used to auto-generate this document (if applicable)"
    )
    published = models.BooleanField(
        default=False,
        help_text="Whether this document has a published PDF"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the PDF was last generated"
    )
    pdf_file = models.FileField(
        upload_to='documents/pdfs/',
        null=True,
        blank=True,
        help_text="Generated PDF file stored in S3/MinIO"
    )
    thumbnail = models.ImageField(
        upload_to='documents/thumbnails/',
        null=True,
        blank=True,
        help_text="Low-res thumbnail of the document generated during publish"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['created_by']),
            models.Index(fields=['published']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def get_pdf_filename(self):
        """Generate filename for PDF"""
        from django.utils.text import slugify
        safe_title = slugify(self.title)
        return f"{safe_title}_{self.user.username}_{self.document_id}.pdf"



# -------------------------
# Enrollment Settings
# -------------------------

class EnrollmentSettings(models.Model):
    """
    Singleton model to control enrollment/registration settings.
    Allows admins to toggle enrollment open/closed and provide a reason.
    """
    id = models.IntegerField(primary_key=True, default=1, editable=False)
    enrollment_open = models.BooleanField(
        default=True,
        help_text="Toggle to enable or disable program enrollment/registration"
    )
    closure_reason = models.TextField(
        blank=True,
        help_text="Optional message to display when enrollment is closed (e.g., 'Registration closed for the season')"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrollment_setting_updates",
        help_text="User who last updated this setting"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Enrollment Settings"
        verbose_name_plural = "Enrollment Settings"
    
    def save(self, *args, **kwargs):
        # Enforce singleton pattern
        self.id = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Prevent deletion of the singleton
        pass
    
    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        obj, created = cls.objects.get_or_create(id=1)
        return obj
    
    def __str__(self):
        status = "OPEN" if self.enrollment_open else "CLOSED"
        return f"Enrollment Settings - {status}"


class RoleEnrollmentRequirement(models.Model):
    """
    Defines enrollment requirements for specific user roles.
    Allows managers to configure which surveys and profile completion
    are required before users of a specific role can register for programs.
    """
    requirement_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=50,
        choices=UserRoleType.choices,
        unique=True,
        help_text="User role this requirement applies to"
    )
    required_surveys = models.ManyToManyField(
        'survey.Survey',
        blank=True,
        related_name="enrollment_requirements",
        help_text="Surveys that must be completed before registration"
    )
    require_profile_completion = models.BooleanField(
        default=True,
        help_text="Whether profile completion is required for registration"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this requirement is currently enforced"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Role Enrollment Requirement"
        verbose_name_plural = "Role Enrollment Requirements"
        ordering = ['role']
    
    def __str__(self):
        return f"Requirements for {self.get_role_display()}"
    
    def check_user_meets_requirements(self, user):
        """
        Check if a user meets all requirements for their role.
        Returns (meets_requirements: bool, missing_items: list)
        """
        if not self.is_active:
            return True, []
        
        missing = []
        
        # Check profile completion
        if self.require_profile_completion and not user.profile_is_complete:
            missing.append("Complete your profile")
        
        # Check required surveys
        from inclusive_world_portal.survey.models import Response
        for survey in self.required_surveys.all():
            # Check if user has completed this survey
            user_responses = Response.objects.filter(
                user=user,
                survey=survey
            )
            if not user_responses.exists():
                missing.append(f"Complete task: {survey.name}")
        
        return len(missing) == 0, missing
