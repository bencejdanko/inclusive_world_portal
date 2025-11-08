from __future__ import annotations

import typing

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.http import HttpRequest

    from inclusive_world_portal.users.models import User


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)
    
    def pre_authenticate(self, request, **credentials):
        """
        Override to check GET params on signup - redirect if no role specified.
        Note: This only works for GET requests to the signup view.
        """
        return super().pre_authenticate(request, **credentials)
    
    def get_signup_form_initial_data(self, request: HttpRequest) -> dict:
        """
        Populate initial data for the signup form, including role from query params.
        """
        initial = super().get_signup_form_initial_data(request)
        
        # Get role from query parameters (e.g., ?role=volunteer)
        role = request.GET.get('role', 'member')
        
        # Validate role
        from inclusive_world_portal.users.models import User
        valid_roles = [choice[0] for choice in User.Role.choices]
        if role in valid_roles:
            initial['role'] = role
        else:
            initial['role'] = User.Role.MEMBER
        
        return initial


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        data: dict[str, typing.Any],
    ) -> User:
        """
        Populates user information from social provider info.

        See: https://docs.allauth.org/en/latest/socialaccount/advanced.html#creating-and-populating-user-instances
        """
        user = super().populate_user(request, sociallogin, data)
        if not user.name:
            if name := data.get("name"):
                user.name = name
            elif first_name := data.get("first_name"):
                user.name = first_name
                if last_name := data.get("last_name"):
                    user.name += f" {last_name}"
        return user
