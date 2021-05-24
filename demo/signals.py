from typing import cast

from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver

from visitors.signals import self_service_visitor_created


@receiver(self_service_visitor_created)
def send_visitor_notification(sender: object, **kwargs: object) -> None:
    visitor = cast(AbstractUser, kwargs["visitor"])
    print(f"Sending visitor pass to: {visitor.email}")
