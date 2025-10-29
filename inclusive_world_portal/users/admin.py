from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm
from .forms import UserAdminCreationForm
from .models import User, DiscoverySurvey

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://docs.allauth.org/en/latest/common/admin.html#admin
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("name", "email", "role")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["username", "name", "role", "is_superuser"]
    list_filter = ["role", "is_staff", "is_superuser", "is_active"]
    search_fields = ["name", "username", "email"]


@admin.register(DiscoverySurvey)
class DiscoverySurveyAdmin(admin.ModelAdmin):
    list_display = ["user", "is_complete", "completed_at", "created_at", "updated_at"]
    list_filter = ["is_complete", "completed_at"]
    search_fields = ["user__username", "user__name", "user__email"]
    readonly_fields = ["created_at", "updated_at", "completed_at"]
    
    fieldsets = (
        ("User & Status", {
            "fields": ("user", "is_complete", "completed_at")
        }),
        ("Section 1: About You", {
            "fields": ("great_things_about_you",),
            "classes": ("collapse",)
        }),
        ("Section 2: Your Team", {
            "fields": ("people_closest_to_you",),
            "classes": ("collapse",)
        }),
        ("Section 3: Things You Like", {
            "fields": (
                "hobbies", "activities", "entertainment", "favorite_food",
                "favorite_people", "favorite_outings", "routines_and_rituals",
                "good_day_description", "bad_day_description", "perfect_day_description"
            ),
            "classes": ("collapse",)
        }),
        ("Section 4: Hopes & Dreams", {
            "fields": ("hopes_and_dreams", "important_to_you", "important_for_you"),
            "classes": ("collapse",)
        }),
        ("Section 5: Learning & Growth", {
            "fields": ("desired_growth_areas", "skills_to_develop", "things_want_to_learn"),
            "classes": ("collapse",)
        }),
        ("Section 6: School & IEP", {
            "fields": ("learned_at_school_liked", "learned_at_school_disliked", "iep_working", "iep_not_working"),
            "classes": ("collapse",)
        }),
        ("Section 7: Communication", {
            "fields": (
                "how_communicate_needs", "what_makes_you_happy", "how_communicate_happy",
                "what_makes_you_sad", "how_communicate_sad", "communication_style"
            ),
            "classes": ("collapse",)
        }),
        ("Section 8: Learning Preferences", {
            "fields": (
                "learning_style", "working_environment_preferences",
                "virtual_learning_help", "supportive_devices"
            ),
            "classes": ("collapse",)
        }),
        ("Section 9: Staff Preferences", {
            "fields": ("ideal_staff_characteristics", "disliked_staff_characteristics"),
            "classes": ("collapse",)
        }),
        ("Section 10: Employment", {
            "fields": (
                "prior_jobs", "jobs_interested_in", "dream_job", "employment_goals",
                "available_to_work_on", "hours_per_week_working"
            ),
            "classes": ("collapse",)
        }),
        ("Section 11: Why IW", {
            "fields": (
                "why_interested_in_iw", "goals_and_expectations", "community_activities_interest",
                "has_ged_or_diploma", "training_courses_completed", "how_heard_about_us"
            ),
            "classes": ("collapse",)
        }),
        ("Section 12: Support Needs", {
            "fields": ("risk_factors", "day_program_recommendations", "form_helper"),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
        }),
    )
    
    def has_add_permission(self, request):
        # Surveys should only be created through the user interface
        return False
