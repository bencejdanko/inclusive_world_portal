"""Form completed view."""
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from ..models import Form


class FormCompleted(TemplateView):
    """View displayed after form completion."""

    template_name = "forms/completed.html"

    def get_context_data(self, **kwargs):
        """Get context data with survey information."""
        context = {}
        survey = get_object_or_404(Form, is_published=True, id=kwargs["id"])
        context["survey"] = survey
        return context
