from django.apps import AppConfig


class DemoConfig(AppConfig):

    name = "demo"

    def ready(self) -> None:
        from . import signals  # noqa: F401

        return super().ready()
