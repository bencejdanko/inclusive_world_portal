"""Survey signals."""
import django.dispatch

# Signal sent when a survey is completed
survey_completed = django.dispatch.Signal()
