"""Question model."""
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .form import Form
from ..settings import CHOICES_SEPARATOR

LOGGER = logging.getLogger(__name__)


CHOICES_HELP_TEXT = _(
    """The choices field is only used if the question type
if the question type is 'radio', 'select', or
'select multiple' provide a comma-separated list of
options for this question ."""
)


def validate_choices(choices):
    """Verify that there are at least two choices.
    
    Args:
        choices: String representing the user choices.
    """
    values = choices.split(CHOICES_SEPARATOR)
    empty = 0
    for value in values:
        if value.replace(" ", "") == "":
            empty += 1
    if len(values) < 2 + empty:
        msg = "The selected field requires an associated list of choices."
        msg += " Choices must contain more than one item."
        raise ValidationError(msg)


class Question(models.Model):
    """A question in a survey."""

    TEXT = "text"
    SHORT_TEXT = "short-text"
    RADIO = "radio"
    SELECT = "select"
    SELECT_IMAGE = "select_image"
    SELECT_MULTIPLE = "select-multiple"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"

    QUESTION_TYPES = (
        (TEXT, _("text (multiple line)")),
        (SHORT_TEXT, _("short text (one line)")),
        (RADIO, _("radio")),
        (SELECT, _("select")),
        (SELECT_MULTIPLE, _("Select Multiple")),
        (SELECT_IMAGE, _("Select Image")),
        (INTEGER, _("integer")),
        (FLOAT, _("float")),
        (DATE, _("date")),
    )

    text = models.TextField(_("Text"))
    order = models.IntegerField(_("Order"))
    required = models.BooleanField(_("Required"))
    survey = models.ForeignKey(Form, on_delete=models.CASCADE, verbose_name=_("Form"), related_name="questions")
    type = models.CharField(_("Type"), max_length=200, choices=QUESTION_TYPES, default=TEXT)
    choices = models.TextField(_("Choices"), blank=True, null=True, help_text=CHOICES_HELP_TEXT)

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")
        ordering = ("survey", "order")

    def save(self, *args, **kwargs):
        """Validate choices before saving."""
        if self.type in [Question.RADIO, Question.SELECT, Question.SELECT_MULTIPLE]:
            # Only validate if choices is not empty
            if self.choices and self.choices.strip():
                validate_choices(self.choices)
        super().save(*args, **kwargs)

    def get_clean_choices(self):
        """Return split and stripped list of choices with no null values."""
        if self.choices is None:
            return []
        choices_list = []
        for choice in self.choices.split(CHOICES_SEPARATOR):
            choice = choice.strip()
            if choice:
                choices_list.append(choice)
        return choices_list

    @property
    def answers_as_text(self):
        """Return answers as a list of text."""
        answers_as_text = []
        for answer in self.answers.all():
            for value in answer.values:
                answers_as_text.append(value)
        return answers_as_text

    def get_choices(self):
        """
        Parse the choices field and return a tuple formatted appropriately
        for the 'choices' argument of a form widget.
        """
        choices_list = []
        for choice in self.get_clean_choices():
            choices_list.append((slugify(choice, allow_unicode=True), choice))
        choices_tuple = tuple(choices_list)
        return choices_tuple

    def __str__(self):
        msg = f"Question '{self.text}' "
        if self.required:
            msg += "(*) "
        msg += f"{self.get_clean_choices()}"
        return msg
