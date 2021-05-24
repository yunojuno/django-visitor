from __future__ import annotations

from typing import Dict

from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject


def visitor(request: HttpRequest) -> Dict[str, SimpleLazyObject]:
    """Add visitor context to template context (if found on the request)."""
    return {"visitor": SimpleLazyObject(lambda: request.visitor)}
