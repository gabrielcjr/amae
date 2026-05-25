import pytest
from django.test import RequestFactory

from pages.context_processors import site_images as site_images_processor
from pages.models import ContactMessage, SiteImage

# --- SiteImage.url property ---


@pytest.mark.django_db
class TestSiteImageUrl:
    def test_returns_external_url_when_no_image(self):
        img = SiteImage.objects.create(
            key="test_ext",
            description="Test",
            external_url="https://example.com/photo.jpg",
        )
        assert img.url == "https://example.com/photo.jpg"

    def test_returns_empty_when_neither(self):
        img = SiteImage.objects.create(
            key="test_empty",
            description="Test",
        )
        assert img.url == ""


# --- site_images context processor ---


@pytest.mark.django_db
class TestSiteImagesContextProcessor:
    def test_returns_dict_keyed_by_slug(self):
        SiteImage.objects.create(
            key="hero", description="Hero", external_url="https://x.com/1.jpg"
        )
        SiteImage.objects.create(
            key="logo", description="Logo", external_url="https://x.com/2.jpg"
        )
        factory = RequestFactory()
        request = factory.get("/")
        result = site_images_processor(request)
        images = result["site_images"]
        assert "hero" in images
        assert "logo" in images
        assert images["hero"].key == "hero"

    def test_empty_when_no_images(self):
        factory = RequestFactory()
        request = factory.get("/")
        result = site_images_processor(request)
        assert result["site_images"] == {}


# --- contact view ---


@pytest.mark.django_db
class TestContactView:
    def test_valid_post_saves_and_shows_success(self, client):
        response = client.post(
            "/contact/",
            {
                "name": "Teste",
                "email": "teste@test.com",
                "subject": "Assunto",
                "message": "Mensagem de teste",
            },
        )
        assert response.status_code == 200
        assert response.context["success"] is True
        assert ContactMessage.objects.count() == 1

    def test_invalid_post_shows_no_success(self, client):
        response = client.post(
            "/contact/",
            {
                "name": "",
                "email": "invalid",
                "subject": "",
                "message": "",
            },
        )
        assert response.status_code == 200
        assert response.context["success"] is False

    def test_success_resets_form(self, client):
        response = client.post(
            "/contact/",
            {
                "name": "Teste",
                "email": "teste@test.com",
                "subject": "Assunto",
                "message": "Mensagem",
            },
        )
        form = response.context["form"]
        assert not form.is_bound


# --- seed management command ---


@pytest.mark.django_db
class TestSeedCommand:
    def test_loads_fixtures(self):
        from django.core.management import call_command

        call_command("seed", verbosity=0)

    def test_refresh_clears_and_reloads(self):
        from django.core.management import call_command

        call_command("seed", verbosity=0)
        call_command("seed", "--refresh", verbosity=0)
