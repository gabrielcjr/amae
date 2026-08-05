import pytest
from django.contrib.auth.models import User

from accounts.forms import (
    EmailAsUsernameForm,
    InvestorRegisterForm,
    MissionaryRegisterForm,
)

# --- EmailAsUsernameForm (base class) ---


@pytest.mark.django_db
class TestEmailAsUsernameForm:
    def test_email_is_required(self):
        form = EmailAsUsernameForm(
            data={
                "first_name": "Teste",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_username_hidden_and_auto_set(self):
        form = EmailAsUsernameForm(
            data={
                "email": "test@test.com",
                "first_name": "Teste",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["username"] == "test@test.com"

    def test_username_field_is_hidden(self):
        form = EmailAsUsernameForm()
        assert form.fields["username"].widget.input_type == "hidden"


# --- InvestorRegisterForm ---


@pytest.mark.django_db
class TestInvestorRegisterForm:
    def test_username_auto_set_to_email(self):
        form = InvestorRegisterForm(
            data={
                "email": "investidor@test.com",
                "first_name": "João Silva",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["username"] == "investidor@test.com"

    def test_email_required(self):
        form = InvestorRegisterForm(
            data={
                "first_name": "João Silva",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_first_name_required(self):
        form = InvestorRegisterForm(
            data={
                "email": "investidor@test.com",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert not form.is_valid()
        assert "first_name" in form.errors

    def test_save_creates_user(self):
        form = InvestorRegisterForm(
            data={
                "email": "investidor@test.com",
                "first_name": "João Silva",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert form.is_valid()
        user = form.save()
        assert user.username == "investidor@test.com"
        assert user.first_name == "João Silva"
        assert hasattr(user, "investor_profile")
        assert user.investor_profile.name == "João Silva"

    def test_first_name_label(self):
        form = InvestorRegisterForm()
        assert form.fields["first_name"].label == "Nome do Investidor"


# --- MissionaryRegisterForm ---


@pytest.mark.django_db
class TestMissionaryRegisterForm:
    def test_username_auto_set_to_email(self):
        form = MissionaryRegisterForm(
            data={
                "email": "joao@test.com",
                "first_name": "João",
                "last_name": "Silva",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["username"] == "joao@test.com"

    def test_last_name_required(self):
        form = MissionaryRegisterForm(
            data={
                "email": "joao@test.com",
                "first_name": "João",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert not form.is_valid()
        assert "last_name" in form.errors

    def test_save_creates_user(self):
        form = MissionaryRegisterForm(
            data={
                "email": "joao@test.com",
                "first_name": "João",
                "last_name": "Silva",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert form.is_valid()
        user = form.save()
        assert user.username == "joao@test.com"
        assert user.last_name == "Silva"
        assert hasattr(user, "missionary_profile")
        assert user.missionary_profile.name == "João Silva"

    def test_field_labels(self):
        form = MissionaryRegisterForm()
        assert form.fields["first_name"].label == "Nome"
        assert form.fields["last_name"].label == "Sobrenome"


# --- Registration views ---


@pytest.mark.django_db
class TestRegisterInvestorView:
    def test_post_creates_user_and_logs_in(self, client):
        response = client.post(
            "/register/investor/",
            {
                "email": "investidor@test.com",
                "first_name": "João Silva",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            },
        )
        assert response.status_code == 302
        assert response.url == "/dashboard/"
        user = User.objects.get(username="investidor@test.com")
        assert hasattr(user, "investor_profile")
        assert "_auth_user_id" in client.session

    def test_get_returns_form(self, client):
        response = client.get("/register/investor/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestRegisterMissionaryView:
    def test_post_creates_user_and_logs_in(self, client):
        response = client.post(
            "/register/missionary/",
            {
                "email": "joao@test.com",
                "first_name": "João",
                "last_name": "Silva",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            },
        )
        assert response.status_code == 302
        assert response.url == "/dashboard/"
        user = User.objects.get(username="joao@test.com")
        assert hasattr(user, "missionary_profile")
        assert "_auth_user_id" in client.session
