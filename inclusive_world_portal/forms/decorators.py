"""Form decorators."""
import logging
from datetime import date
from functools import wraps

from django.contrib import messages
from django.shortcuts import Http404, get_object_or_404, redirect, reverse
from django.utils.translation import gettext_lazy as _

from .models import Form


def survey_available(func):
    """Check if a form is available (published and not expired). Use this as a decorator for view functions."""

    @wraps(func)
    def survey_check(self, request, *args, **kwargs):
        survey = get_object_or_404(
            Form.objects.prefetch_related("questions"), is_published=True, id=kwargs["id"]
        )
        if not survey.is_published:
            raise Http404
        if survey.expire_date < date.today():
            msg = "Form is not published anymore. It was published until: '%s'."
            logging.warning(msg, survey.expire_date)
            messages.warning(request, _("This form has expired for new submissions."))
            return redirect(reverse("survey-list"))
        if survey.publish_date > date.today():
            msg = "Form is not yet published. It is due: '%s'."
            logging.warning(msg, survey.publish_date)
            raise Http404
        return func(self, request, *args, **kwargs, survey=survey)

    return survey_check
