"""Index view for form list."""
from datetime import date

from django.views.generic import TemplateView

from ..models import Form


class IndexView(TemplateView):
    """Display list of available forms."""

    template_name = "forms/list.html"

    def get_context_data(self, **kwargs):
        """Get context data with available forms."""
        context = super().get_context_data(**kwargs)
        surveys = Form.objects.filter(
            is_published=True, expire_date__gte=date.today(), publish_date__lte=date.today()
        )
        if not self.request.user.is_authenticated:
            surveys = surveys.filter(need_logged_user=False)
        context["surveys"] = surveys
        return context
