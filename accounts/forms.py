from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from missions.models import Investor, Missionary


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

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if (
            User.objects.filter(username__iexact=email).exists()
            or User.objects.filter(email__iexact=email).exists()
        ):
            raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email

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

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            Investor.objects.get_or_create(
                user=user,
                defaults={
                    "name": user.first_name,
                    "contact_email": user.email,
                },
            )
        return user


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

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            full_name = f"{user.first_name} {user.last_name}".strip()
            Missionary.objects.get_or_create(
                user=user,
                defaults={
                    "name": full_name,
                },
            )
        return user
