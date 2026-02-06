import pytest
from django.contrib.auth.models import User

from accounts.forms import ChurchRegisterForm, MissionaryRegisterForm

# --- ChurchRegisterForm ---


@pytest.mark.django_db
class TestChurchRegisterForm:
    def test_username_auto_set_to_email(self):
        form = ChurchRegisterForm(
            data={
                "email": "igreja@test.com",
                "first_name": "Igreja Teste",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["username"] == "igreja@test.com"

    def test_email_required(self):
        form = ChurchRegisterForm(
            data={
                "first_name": "Igreja Teste",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_first_name_required(self):
        form = ChurchRegisterForm(
            data={
                "email": "igreja@test.com",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert not form.is_valid()
        assert "first_name" in form.errors

    def test_save_creates_user(self):
        form = ChurchRegisterForm(
            data={
                "email": "igreja@test.com",
                "first_name": "Igreja Teste",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            }
        )
        assert form.is_valid()
        user = form.save()
        assert user.username == "igreja@test.com"
        assert user.first_name == "Igreja Teste"


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


# --- Registration views ---


@pytest.mark.django_db
class TestRegisterChurchView:
    def test_post_creates_user_and_logs_in(self, client):
        response = client.post(
            "/cadastrar/igreja/",
            {
                "email": "igreja@test.com",
                "first_name": "Igreja Teste",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            },
        )
        assert response.status_code == 302
        assert response.url == "/campos-missionarios/"
        assert User.objects.filter(username="igreja@test.com").exists()
        # Check user is logged in (session has _auth_user_id)
        assert "_auth_user_id" in client.session

    def test_get_returns_form(self, client):
        response = client.get("/cadastrar/igreja/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestRegisterMissionaryView:
    def test_post_creates_user_and_logs_in(self, client):
        response = client.post(
            "/cadastrar/missionario/",
            {
                "email": "joao@test.com",
                "first_name": "João",
                "last_name": "Silva",
                "password1": "Str0ngP@ss!",
                "password2": "Str0ngP@ss!",
            },
        )
        assert response.status_code == 302
        assert response.url == "/campos-missionarios/"
        assert User.objects.filter(username="joao@test.com").exists()
        assert "_auth_user_id" in client.session
