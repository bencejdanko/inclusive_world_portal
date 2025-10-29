from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from inclusive_world_portal.users.forms import UserProfileForm
from inclusive_world_portal.users.models import User
from inclusive_world_portal.users.opd_utils import generate_opd_editor_url


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    success_message = _("Profile successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None=None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()


class OPDEditorRedirectView(LoginRequiredMixin, RedirectView):
    """
    Redirect view that generates a JWT token and sends the user to the OPD collaborative editor.
    This view intercepts the "One Page Description" link and mints a secure token for accessing
    the frontend editor with appropriate role-based permissions.
    """
    permanent = False

    def get_redirect_url(self, *args, **kwargs) -> str:
        """
        Generate OPD editor URL with JWT authentication token.
        
        Returns:
            URL to the OPD editor frontend with embedded JWT token
        """
        user = self.request.user
        
        try:
            # Generate the authenticated editor URL
            opd_url = generate_opd_editor_url(user)
            
            # Log the access for audit purposes
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f"User {user.username} (role: {user.role}) accessing OPD editor"
            )
            
            return opd_url
            
        except ValueError as e:
            # Handle configuration errors (missing OPD_SERVER or OPD_SECRET)
            messages.error(
                self.request,
                _("One Page Description editor is not configured. Please contact support.")
            )
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"OPD configuration error: {e}")
            
            # Redirect back to the dashboard on error
            return reverse("users:dashboard")


opd_editor_redirect_view = OPDEditorRedirectView.as_view()
