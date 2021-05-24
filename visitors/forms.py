from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class SelfServiceForm(forms.Form):
    """Form for capturing user info."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=True)
    vuid = forms.CharField(widget=forms.HiddenInput())

    def clean_email(self) -> str:
        email = self.cleaned_data["email"]
        if email.endswith("example.com"):
            raise ValidationError(
                _("Invalid email - you cannot use the example.com domain")
            )
        return email
