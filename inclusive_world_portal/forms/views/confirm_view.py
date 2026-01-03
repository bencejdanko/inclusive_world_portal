"""Confirmation view for form responses."""
from django.views.generic import TemplateView

from ..models import Response


class ConfirmView(TemplateView):
    """View for confirming form submission."""

    template_name = "forms/confirm.html"

    def get_context_data(self, **kwargs):
        """Get context data with response information."""
        context = super().get_context_data(**kwargs)
        context["uuid"] = str(kwargs["uuid"])
        context["response"] = Response.objects.get(interview_uuid=context["uuid"])
        return context
