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
# Roles
# -------------------------

class UserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roles")
    role = models.CharField(max_length=32, choices=UserRoleType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("user", "role"),)
        indexes = [
            models.Index(fields=["user", "role"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.role}"

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
    """
    document_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    title = models.CharField(max_length=255, default="Untitled Document")
    content = models.TextField(blank=True, help_text="HTML content from Quill editor")
    state = models.CharField(
        max_length=16,
        choices=DocumentState.choices,
        default=DocumentState.DRAFT,
        help_text="Current state of the document"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class DocumentExport(models.Model):
    """
    Tracks PDF exports of documents.
    Stores the exported PDF file and metadata.
    Users can have multiple exports and toggle which one is "active".
    
    Storage Configuration:
    - By default, uses Django's default file storage (STORAGES["default"])
    - For production with S3/MinIO, configure in settings:
        STORAGES = {
            "default": {
                "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
                "OPTIONS": {
                    "access_key": env("AWS_ACCESS_KEY_ID"),
                    "secret_key": env("AWS_SECRET_ACCESS_KEY"),
                    "bucket_name": env("AWS_STORAGE_BUCKET_NAME"),
                    "endpoint_url": env("AWS_S3_ENDPOINT_URL"),  # For MinIO
                    "region_name": env("AWS_S3_REGION_NAME", default="us-east-1"),
                },
            },
        }
    - Install: pip install django-storages boto3
    """
    export_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_exports"
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="exports"
    )
    # File stored in media/document_exports/<user_id>/<filename>
    file = models.FileField(
        upload_to='document_exports/%Y/%m/%d/',
        help_text="PDF file of the document export"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Whether this is the currently active OPD for the user"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['document', '-created_at']),
        ]
    
    def __str__(self):
        active_status = " (Active)" if self.is_active else ""
        return f"{self.document.title} - {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}{active_status}"
    
    def get_filename(self):
        """Return a user-friendly filename for download."""
        import os
        return os.path.basename(self.file.name)


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
