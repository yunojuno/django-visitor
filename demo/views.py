from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse

from visitors.decorators import user_is_visitor


def index(request: HttpRequest) -> HttpResponse:
    """Display the homepage."""
    return render(request, template_name="index.html")


# Test view that requires a valid Visitor Pass
@user_is_visitor(scope="foo")
def foo(request: HttpRequest) -> HttpResponse:
    return HttpResponse("OK")


# Test view that supports self-service
@user_is_visitor(scope="bar", self_service=True)
def bar(request: HttpRequest) -> HttpResponse:
    return render(request, template_name="bar.html")


# Deactivate any current visitor token - this is analagous
# to "logging out" an authenticated user.
def logout(request: HttpRequest) -> HttpResponse:
    if request.user.is_visitor:
        request.visitor.deactivate()
    return HttpResponseRedirect(reverse("bar"))
