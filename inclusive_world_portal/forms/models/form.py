"""Form model."""
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from ..settings import DEFAULT_SURVEY_PUBLISHING_DURATION


def in_duration_day():
    """Calculate default expiration date."""
    return now() + timedelta(days=DEFAULT_SURVEY_PUBLISHING_DURATION)


class Form(models.Model):
    """A form with questions that users can answer."""

    ALL_IN_ONE_PAGE = 0
    BY_QUESTION = 1

    DISPLAY_METHOD_CHOICES = [
        (BY_QUESTION, _("By question")),
        (ALL_IN_ONE_PAGE, _("All in one page")),
    ]

    name = models.CharField(_("Name"), max_length=400)
    description = models.TextField(_("Description"))
    is_published = models.BooleanField(_("Users can see it and answer it"), default=True)
    need_logged_user = models.BooleanField(_("Only authenticated users can see it and answer it"))
    editable_answers = models.BooleanField(_("Users can edit their answers afterwards"), default=True)
    display_method = models.SmallIntegerField(
        _("Display method"), choices=DISPLAY_METHOD_CHOICES, default=ALL_IN_ONE_PAGE
    )
    template = models.CharField(_("Template"), max_length=255, null=True, blank=True)
    publish_date = models.DateField(_("Publication date"), blank=True, null=False, default=now)
    expire_date = models.DateField(_("Expiration date"), blank=True, null=False, default=in_duration_day)
    redirect_url = models.URLField(_("Redirect URL"), blank=True)

    class Meta:
        verbose_name = _("form")
        verbose_name_plural = _("forms")

    def __str__(self):
        return str(self.name)

    @property
    def safe_name(self):
        """Return a safe file name version of the form name."""
        return self.name.replace(" ", "_").encode("utf-8").decode("ISO-8859-1")

    def latest_answer_date(self):
        """Return the latest answer date. Return None if there is no response."""
        min_ = None
        for response in self.responses.all():
            if min_ is None or min_ < response.updated:
                min_ = response.updated
        return min_

    def get_absolute_url(self):
        """Return the URL to view this form."""
        return reverse("forms:survey-detail", kwargs={"id": self.pk})

    def is_all_in_one_page(self):
        """Check if form displays all questions on one page."""
        return self.display_method == self.ALL_IN_ONE_PAGE
