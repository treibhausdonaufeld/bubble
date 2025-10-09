from __future__ import annotations

import typing

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth.models import Group

from bubble.core.permissions_config import DefaultGroup

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.http import HttpRequest

    from bubble.users.models import User


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> bool:
        return getattr(settings, "SOCIALACCOUNT_ALLOW_REGISTRATION", True)

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

    def save_user(self, request, sociallogin, form=None):
        """
        Add user to default group
        """
        user = super().save_user(request, sociallogin, form)

        # add to default group
        default_group, _ = Group.objects.get_or_create(name=DefaultGroup.DEFAULT)
        user.groups.add(default_group)

        # check for internal group
        groups = sociallogin.account.extra_data.get("userinfo", {}).get("groups", [])
        provider_internal_group_name = sociallogin.provider.app.settings.get(
            "internal_group_name", ""
        )

        if provider_internal_group_name in groups:
            internal_group, _ = Group.objects.get_or_create(name=DefaultGroup.INTERNAL)
            user.groups.add(internal_group)
            profile = user.profile
            profile.internal = True
            profile.save()

        provider_admin_group_name = sociallogin.provider.app.settings.get(
            "admin_group_name", ""
        )

        if provider_admin_group_name in groups:
            internal_group, _ = Group.objects.get_or_create(
                name=DefaultGroup.ADMINISTRATORS
            )
            user.groups.add(internal_group)
            user.is_staff = True
            user.is_superuser = True
            user.save()

        return user
