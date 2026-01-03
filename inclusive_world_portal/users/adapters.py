from __future__ import annotations

import typing

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

if typing.TYPE_CHECKING:
    from django.http import HttpRequest

    from inclusive_world_portal.users.models import User


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

