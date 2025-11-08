from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.utils.translation import gettext_lazy as _

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        error_messages = {
            "username": {"unique": _("This username has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """
    
    role = forms.ChoiceField(
        choices=User.Role.choices,
        initial=User.Role.MEMBER,
        widget=forms.HiddenInput(),
        required=False,
    )
    
    def save(self, request):
        user = super().save(request)
        # Get role from cleaned_data first, then fall back to request GET params
        role = self.cleaned_data.get('role')
        if not role or role == User.Role.MEMBER:
            # Check if a different role was specified in the URL
            role = request.GET.get('role', User.Role.MEMBER)
            # Validate the role
            valid_roles = [choice[0] for choice in User.Role.choices]
            if role not in valid_roles:
                role = User.Role.MEMBER
        user.role = role
        user.save()
        return user


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """


class UserProfileForm(forms.ModelForm):
    """
    Form for users to update their profile information.
    """
    
    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "phone_no",
            "bio",
            "age",
            "grade",
            "profile_picture",
            "parent_guardian_name",
            "parent_guardian_phone",
            "parent_guardian_email",
            "emergency_contact_first_name",
            "emergency_contact_last_name",
            "emergency_contact_relationship",
            "emergency_contact_phone",
            "emergency_contact_secondary_phone",
            "emergency_contact_email",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "email": _("Optional - for account recovery and notifications."),
            "profile_picture": _("Upload a profile picture (optional)."),
        }
