from __future__ import annotations

from unittest import mock

from django.http import HttpRequest

from visitors import context_processors
from visitors.models import Visitor


class TestVisitorContextProcessor:
    def test_visitor(self):
        request = HttpRequest()
        request.visitor = mock.Mock(spec=Visitor)
        assert context_processors.visitor(request)["visitor"] == request.visitor

    def test_no_visitor(self):
        request = HttpRequest()
        request.visitor = None
        assert context_processors.visitor(request)["visitor"] == request.visitor
