from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class EmailAsUsernameForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["email"].label = "E-mail"
        self.fields["username"].required = False
        self.fields["username"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["username"] = cleaned_data.get("email", "")
        self.instance.username = cleaned_data["username"]
        return cleaned_data


class InvestorRegisterForm(EmailAsUsernameForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["first_name"].label = "Nome do Investidor"


class MissionaryRegisterForm(EmailAsUsernameForm):
    class Meta(EmailAsUsernameForm.Meta):
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["first_name"].label = "Nome"
        self.fields["last_name"].required = True
        self.fields["last_name"].label = "Sobrenome"
