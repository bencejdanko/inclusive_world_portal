"""Answer model."""
import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .question import Question
from .response import Response

LOGGER = logging.getLogger(__name__)


class Answer(models.Model):
    """An answer to a survey question."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name=_("Question"), related_name="answers")
    response = models.ForeignKey(Response, on_delete=models.CASCADE, verbose_name=_("Response"), related_name="answers")
    created = models.DateTimeField(_("Creation date"), auto_now_add=True)
    updated = models.DateTimeField(_("Update date"), auto_now=True)
    body = models.TextField(_("Content"), blank=True, null=True)

    def __init__(self, *args, **kwargs):
        try:
            question = Question.objects.get(pk=kwargs["question_id"])
        except KeyError:
            question = kwargs.get("question")
        body = kwargs.get("body")
        if question and body:
            self.check_answer_body(question, body)
        super().__init__(*args, **kwargs)

    @property
    def values(self):
        """Return the answer values as a list."""
        if self.body is None:
            return [None]
        if len(self.body) < 3 or self.body[0:3] != "[u'":
            return [self.body]
        # Parse the body for multiple values
        values = []
        raw_values = self.body.split("', u'")
        nb_values = len(raw_values)
        for i, value in enumerate(raw_values):
            if i == 0:
                value = value[3:]
            if i + 1 == nb_values:
                value = value[:-2]
            values.append(value)
        return values

    def check_answer_body(self, question, body):
        """Validate answer body based on question type."""
        if question.type in [Question.RADIO, Question.SELECT, Question.SELECT_MULTIPLE]:
            choices = question.get_clean_choices()
            self.check_answer_for_select(choices, body)
        if question.type == Question.INTEGER and body and body != "":
            try:
                body = int(body)
            except ValueError as e:
                msg = "Answer is not an integer"
                raise ValidationError(msg) from e
        if question.type == Question.FLOAT and body and body != "":
            try:
                body = float(body)
            except ValueError as e:
                msg = "Answer is not a number"
                raise ValidationError(msg) from e

    def check_answer_for_select(self, choices, body):
        """Validate answer for select-type questions."""
        answers = []
        if body:
            if body[0] == "[":
                for i, part in enumerate(body.split("'")):
                    if i % 2 == 1:
                        answers.append(part)
            else:
                answers = [body]
        for answer in answers:
            if answer not in choices:
                msg = f"Impossible answer '{body}'"
                msg += f" should be in {choices} "
                raise ValidationError(msg)

    def __str__(self):
        return f"{self.__class__.__name__} to '{self.question}' : '{self.body}'"
