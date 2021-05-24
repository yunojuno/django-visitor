from __future__ import annotations

import uuid

from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View

from visitors.exceptions import InvalidVisitorPass

from .forms import SelfServiceForm
from .models import Visitor
from .signals import self_service_visitor_created


class SelfService(View):
    """
    Enable users to create their own visitor passes.

    If a visitor pass is marked as `auto-enroll` then a user can
    create their own pass. In this model, an user without access
    would be redirected to this view, where they can input their
    own name and email. They receive their own visitor pass.

    The purpose of this is to add some protection to 'obscure'
    urls. e.g. those that rely on an unguessable uuid - instead
    of making those URLs completely public, we can force the user
    to give us their name / email (name can be faked, but they
    will require access to the email).

    """

    def get(self, request: HttpRequest, visitor_uuid: uuid.UUID) -> HttpResponse:
        """Render the initial form."""
        visitor = get_object_or_404(Visitor, uuid=visitor_uuid)
        if visitor.is_active:
            raise InvalidVisitorPass("Visitor pass has already been activated")
        if visitor.has_expired:
            raise InvalidVisitorPass("Visitor pass has expired")
        form = SelfServiceForm(initial={"vuid": visitor.uuid})
        return render(
            request,
            template_name="visitors/self_service_request.html",
            context={"visitor": visitor, "form": form},
        )

    def post(self, request: HttpRequest, visitor_uuid: uuid.UUID) -> HttpResponse:
        """
        Process the form and send the pass email.

        The core function here is to update the visitor object with
        the details from the form. Once that is done the visitor
        pass is active and can be sent to the user. This view fires
        the `self_service_visitor_created` signal - you should use
        this to send out the notification.

        """
        visitor = get_object_or_404(Visitor, uuid=visitor_uuid)
        form = SelfServiceForm(request.POST)
        if form.is_valid():
            visitor.first_name = form.cleaned_data["first_name"]
            visitor.last_name = form.cleaned_data["last_name"]
            visitor.email = form.cleaned_data["email"]
            visitor.reactivate()
            # hook into this to send the email notification to the user.
            self_service_visitor_created.send(sender=self.__class__, visitor=visitor)
            url = reverse(
                "visitors:self-service-success",
                kwargs={"visitor_uuid": visitor_uuid},
            )
            return HttpResponseRedirect(url)
        return render(
            request,
            template_name="visitors/self_service_request.html",
            context={
                "visitor": visitor,
                "form": form,
            },
        )


def self_service_success(request: HttpRequest, visitor_uuid: uuid.UUID) -> HttpResponse:
    """Display the success page."""
    visitor = get_object_or_404(Visitor, uuid=visitor_uuid)
    return render(
        request,
        template_name="visitors/self_service_success.html",
        context={"visitor": visitor},
    )
