"""Form forms."""
import logging
import uuid

from django import forms
from django.forms import models, inlineformset_factory
from django.urls import reverse
from django.utils.text import slugify

from .models import Answer, Question, Response, Form
from .signals import survey_completed
from .widgets import ImageSelectWidget
from .settings import CHOICES_SEPARATOR

LOGGER = logging.getLogger(__name__)


class SurveyForm(forms.ModelForm):
    """Form for creating/editing surveys."""
    
    class Meta:
        model = Form
        fields = [
            'name', 'description', 'is_published', 'need_logged_user',
            'editable_answers', 'display_method', 'template',
            'publish_date', 'expire_date', 'redirect_url'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'need_logged_user': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'editable_answers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_method': forms.Select(attrs={'class': 'form-select'}),
            'template': forms.TextInput(attrs={'class': 'form-control'}),
            'publish_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'redirect_url': forms.URLInput(attrs={'class': 'form-control'}),
        }


class QuestionForm(forms.ModelForm):
    """Form for questions."""
    
    class Meta:
        model = Question
        fields = ['text', 'order', 'required', 'type', 'choices']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'choices': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# Formset for inline editing
QuestionFormSet = inlineformset_factory(
    Form, Question, form=QuestionForm,
    extra=1, can_delete=True
)


class ResponseForm(models.ModelForm):
    """Form for responding to a survey."""

    FIELDS = {
        Question.TEXT: forms.CharField,
        Question.SHORT_TEXT: forms.CharField,
        Question.SELECT_MULTIPLE: forms.MultipleChoiceField,
        Question.INTEGER: forms.IntegerField,
        Question.FLOAT: forms.FloatField,
        Question.DATE: forms.DateField,
    }

    WIDGETS = {
        Question.TEXT: forms.Textarea,
        Question.SHORT_TEXT: forms.TextInput,
        Question.RADIO: forms.RadioSelect,
        Question.SELECT: forms.Select,
        Question.SELECT_IMAGE: ImageSelectWidget,
        Question.SELECT_MULTIPLE: forms.CheckboxSelectMultiple,
    }

    class Meta:
        model = Response
        fields = ()

    def __init__(self, *args, **kwargs):
        """Initialize form with survey object."""
        self.survey = kwargs.pop("survey")
        self.user = kwargs.pop("user")
        try:
            self.step = int(kwargs.pop("step"))
        except KeyError:
            self.step = None
        super().__init__(*args, **kwargs)
        self.uuid = uuid.uuid4().hex

        if self.survey.display_method == Form.BY_QUESTION:
            self.steps_count = len(self.survey.questions.all())
        else:
            self.steps_count = 1
        # Will contain prefetched data to avoid multiple db calls
        self.response = False
        self.answers = False

        self.add_questions(kwargs.get("data"))

        self._get_preexisting_response()

        if not self.survey.editable_answers and self.response is not None:
            for name in self.fields.keys():
                self.fields[name].widget.attrs["disabled"] = True

    def add_questions(self, data):
        """Add a field for each survey question, corresponding to the question type as appropriate."""
        for i, question in enumerate(self.survey.questions.all()):
            not_to_keep = i != self.step and self.step is not None
            if self.survey.display_method == Form.BY_QUESTION and not_to_keep:
                continue
            self.add_question(question, data)

    def current_categories(self):
        """Return categories for the current step - deprecated, returns empty list."""
        return []

    def _get_preexisting_response(self):
        """Recover a pre-existing response in database."""
        if self.response:
            return self.response

        if not self.user.is_authenticated:
            self.response = None
        else:
            try:
                self.response = Response.objects.prefetch_related("user", "survey").get(
                    user=self.user, survey=self.survey
                )
            except Response.DoesNotExist:
                LOGGER.debug("No saved response for '%s' for user %s", self.survey, self.user)
                self.response = None
        return self.response

    def _get_preexisting_answers(self):
        """Recover pre-existing answers in database."""
        if self.answers:
            return self.answers

        response = self._get_preexisting_response()
        if response is None:
            self.answers = None
        try:
            answers = Answer.objects.filter(response=response).prefetch_related("question")
            self.answers = {answer.question.id: answer for answer in answers.all()}
        except Answer.DoesNotExist:
            self.answers = None

        return self.answers

    def _get_preexisting_answer(self, question):
        """Recover a pre-existing answer in database for a specific question."""
        answers = self._get_preexisting_answers()
        return answers.get(question.id, None)

    def get_question_initial(self, question, data):
        """Get the initial value that we should use in the Form."""
        initial = None
        answer = self._get_preexisting_answer(question)
        if answer:
            # Initialize the field with values from the database if any
            if question.type == Question.SELECT_MULTIPLE:
                initial = []
                if answer.body == "[]":
                    pass
                elif "[" in answer.body and "]" in answer.body:
                    initial = []
                    unformated_choices = answer.body[1:-1].strip()
                    for unformated_choice in unformated_choices.split(CHOICES_SEPARATOR):
                        choice = unformated_choice.split("'")[1]
                        initial.append(slugify(choice))
                else:
                    # Only one element
                    initial.append(slugify(answer.body))
            else:
                initial = answer.body
        if data:
            # Initialize the field field from a POST request, if any.
            # Replace values from the database
            initial = data.get(f"question_{question.pk}")
        return initial

    def get_question_widget(self, question):
        """Return the widget we should use for a question."""
        try:
            return self.WIDGETS[question.type]
        except KeyError:
            return None

    @staticmethod
    def get_question_choices(question):
        """Return the choices we should use for a question."""
        qchoices = None
        if question.type not in [Question.TEXT, Question.SHORT_TEXT, Question.INTEGER, Question.FLOAT, Question.DATE]:
            qchoices = question.get_choices()
            # Add an empty option at the top so that the user has to explicitly select one
            if question.type in [Question.SELECT, Question.SELECT_IMAGE]:
                qchoices = tuple([("", "-------------")]) + qchoices
        return qchoices

    def get_question_field(self, question, **kwargs):
        """Return the field we should use in our form."""
        try:
            return self.FIELDS[question.type](**kwargs)
        except KeyError:
            return forms.ChoiceField(**kwargs)

    def add_question(self, question, data):
        """Add a question to the form."""
        kwargs = {"label": question.text, "required": question.required}
        initial = self.get_question_initial(question, data)
        if initial:
            kwargs["initial"] = initial
        choices = self.get_question_choices(question)
        if choices:
            kwargs["choices"] = choices
        widget = self.get_question_widget(question)
        if widget:
            kwargs["widget"] = widget
        field = self.get_question_field(question, **kwargs)

        if question.type == Question.DATE:
            field.widget.attrs["class"] = "date"
        self.fields[f"question_{question.pk}"] = field

    def has_next_step(self):
        """Check if there is a next step in the survey."""
        if not self.survey.is_all_in_one_page():
            if self.step < self.steps_count - 1:
                return True
        return False

    def next_step_url(self):
        """Get the URL for the next step."""
        if self.has_next_step():
            context = {"id": self.survey.id, "step": self.step + 1}
            return reverse("survey-detail-step", kwargs=context)

    def current_step_url(self):
        """Get the URL for the current step."""
        return reverse("survey-detail-step", kwargs={"id": self.survey.id, "step": self.step})

    def save(self, commit=True):
        """Save the response object."""
        # Recover an existing response from the database if any
        response = self._get_preexisting_response()
        if not self.survey.editable_answers and response is not None:
            return None
        if response is None:
            response = super().save(commit=False)
        response.survey = self.survey
        response.interview_uuid = self.uuid
        if self.user.is_authenticated:
            response.user = self.user
        response.save()
        # Response "raw" data as dict (for signal)
        data = {"survey_id": response.survey.id, "interview_uuid": response.interview_uuid, "responses": []}
        # Create an answer object for each question and associate it with this response
        for field_name, field_value in list(self.cleaned_data.items()):
            if field_name.startswith("question_"):
                # Extract the question id from the field name
                q_id = int(field_name.split("_")[1])
                question = Question.objects.get(pk=q_id)
                answer = self._get_preexisting_answer(question)
                if answer is None:
                    answer = Answer(question=question)
                if question.type == Question.SELECT_IMAGE:
                    value, img_src = field_value.split(":", 1)
                    # TODO Handling of SELECT IMAGE
                    LOGGER.debug("Question.SELECT_IMAGE not implemented, please use : %s and %s", value, img_src)
                answer.body = field_value
                data["responses"].append((answer.question.id, answer.body))
                LOGGER.debug("Creating answer for question %d of type %s : %s", q_id, answer.question.type, field_value)
                answer.response = response
                answer.save()
        survey_completed.send(sender=Response, instance=response, data=data)
        return response
