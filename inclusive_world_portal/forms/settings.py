"""Survey application settings."""
from django.conf import settings

# User-facing string when no answer is provided
USER_DID_NOT_ANSWER = getattr(settings, "USER_DID_NOT_ANSWER", "Left blank")

# Separator for multiple choice options
CHOICES_SEPARATOR = getattr(settings, "CHOICES_SEPARATOR", ",")

# CSV export compatibility for Excel
EXCEL_COMPATIBLE_CSV = getattr(settings, "EXCEL_COMPATIBLE_CSV", False)

# Default survey publishing duration in days
DEFAULT_SURVEY_PUBLISHING_DURATION = getattr(settings, "DEFAULT_SURVEY_PUBLISHING_DURATION", 7)
