"""Forms admin configuration."""
from django.contrib import admin

from .models import Answer, Question, Response, Form


class QuestionInline(admin.StackedInline):
    """Inline admin for questions within a form."""

    model = Question
    ordering = ("order",)
    extra = 1


class FormAdmin(admin.ModelAdmin):
    """Admin interface for forms."""

    list_display = ("name", "is_published", "need_logged_user", "template")
    list_filter = ("is_published", "need_logged_user")
    inlines = [QuestionInline]


class AnswerBaseInline(admin.StackedInline):
    """Inline admin for answers within a response."""

    fields = ("question", "body")
    readonly_fields = ("question",)
    extra = 0
    model = Answer


class ResponseAdmin(admin.ModelAdmin):
    """Admin interface for form responses."""

    list_display = ("interview_uuid", "survey", "created", "user")
    list_filter = ("survey", "created")
    date_hierarchy = "created"
    inlines = [AnswerBaseInline]
    readonly_fields = ("survey", "created", "updated", "interview_uuid", "user")


admin.site.register(Form, FormAdmin)
admin.site.register(Response, ResponseAdmin)
