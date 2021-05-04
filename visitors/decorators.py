from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _

from .exceptions import VisitorAccessDenied
from .models import Visitor, VisitorLog

logger = logging.getLogger(__name__)

# universal scope - essentially unscoped access
SCOPE_ANY = "*"

# for typing
BypassFunc = Callable[[HttpRequest], bool]


def is_visitor(user: settings.AUTH_USER_MODEL) -> bool:
    """Shortcut function for use with user_passes_test decorator."""
    return user.is_visitor


def is_staff(user: settings.AUTH_USER_MODEL) -> bool:
    """Shortcut function for use with user_passes_test decorator."""
    return user.is_staff


def is_superuser(user: settings.AUTH_USER_MODEL) -> bool:
    """Shortcut function for use with user_passes_test decorator."""
    return user.is_superuser


def is_authenticated(user: settings.AUTH_USER_MODEL) -> bool:
    """Shortcut function for use with user_passes_test decorator."""
    return user.is_authenticated


def _get_request_arg(*args: Any) -> Optional[HttpRequest]:
    """Extract the arg that is an HttpRequest object."""
    for arg in args:
        if isinstance(arg, HttpRequest):
            return arg
    return None


def user_is_visitor(  # noqa: C901
    view_func: Optional[Callable] = None,
    scope: str = "",
    bypass_func: Optional[BypassFunc] = None,
    log_visit: bool = True,
    self_service: bool = False,
) -> Callable:
    """
    Decorate view functions that supports Visitor access.

    The 'scope' param is mapped to the request.visitor.scope attribute - if
    the scope is SCOPE_ANY then this is ignored.

    The 'bypass_func' is a callable that can be used to provide exceptions
    to the scope - e.g. allowing authenticate users, or staff, to bypass the
    visitor restriction. Defaults to None (only visitors with appropriate
    scope allowed).

    The 'log_visit' arg can be used to override the default logging - if this
    is too noisy, for instance.

    If 'self_service' is True, then instead of a straight PermissionDenied error
    we raise VisitorAccessDenied, passing along the scope. This is then picked
    up in the middleware, and the user redirected to a page where they can
    enter their details and effectively invite themselves. Caveat emptor.

    """
    if not scope:
        raise ValueError("Decorator scope cannot be empty.")

    if view_func is None:
        return functools.partial(
            user_is_visitor,
            scope=scope,
            bypass_func=bypass_func,
            log_visit=log_visit,
            self_service=self_service,
        )

    @functools.wraps(view_func)
    def inner(*args: Any, **kwargs: Any) -> HttpResponse:
        # should never happen, but keeps mypy happy as it _could_
        if not view_func:
            raise ValueError("Callable (view_func) missing.")

        # HACK: if this is decorating a method, then the first arg will be
        # the object (self), and not the request. In order to make this work
        # with functions and methods we need to determine where the request
        # arg is.
        request = _get_request_arg(*args)
        if not request:
            raise ValueError("Request argument missing.")

        # Allow custom rules to bypass the visitor checks
        if bypass_func and bypass_func(request):
            return view_func(*args, **kwargs)

        def _raise_or_redirect(message: str) -> HttpResponseRedirect:
            """Redirect to self-service page if appropriate."""
            if self_service:
                return redirect_to_self_service(request, scope)
            raise VisitorAccessDenied(_(message), scope=scope)

        # Do we have a visitor?
        if not request.user.is_visitor:
            return _raise_or_redirect("Visitor access denied")

        # Check the function scope matches (or is "*")
        if scope not in (SCOPE_ANY, request.visitor.scope):
            # We have a visitor with the wrong scope
            return _raise_or_redirect("Visitor access denied (invalid scope)")

        response = view_func(*args, **kwargs)
        if log_visit:
            VisitorLog.objects.create_log(request, response.status_code)
        return response

    return inner


def redirect_to_self_service(request: HttpRequest, scope: str) -> HttpResponseRedirect:
    """Create inactive Visitor token and redirect to enable self-service."""
    # create an inactive token for the time being. This will be used by
    # the auto-enroll view. The user fills in their name and email, which
    # overwrites the blank values here, and sets the token to be active.
    visitor = Visitor.objects.create(
        email="anon@example.com",
        scope=scope,
        is_active=False,
        context={"self-service": True},
    )
    return HttpResponseRedirect(
        reverse(
            "visitors:self-service",
            kwargs={"visitor_uuid": visitor.uuid},
        )
        + f"?next={request.get_full_path()}"
    )
