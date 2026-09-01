import pytest
from django.urls import reverse
from django.utils import translation

from finance.models import TransactionType
from missions.models import Adoption, BrazilianRegion, MissionField


@pytest.mark.django_db
class TestI18nLanguageSwitching:
    def test_default_language_is_english(self, client):
        response = client.get(reverse("home"))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Connecting Investors and Missionaries" in content
        assert "How It Works" in content
        assert "Mission Fields" in content
        assert "Log in" in content

    def test_set_language_to_portuguese_via_post(self, client):
        # Post to standard Django set_language endpoint
        set_lang_url = reverse("set_language")
        response = client.post(
            set_lang_url,
            data={"language": "pt-br", "next": reverse("home")},
            follow=True,
        )
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Conectando Investidores e Missionários" in content
        assert "Como Funciona" in content
        assert "Campos Missionários" in content
        assert "Entrar" in content

    def test_switch_back_to_english(self, client):
        set_lang_url = reverse("set_language")
        # First set to pt-br
        client.post(set_lang_url, data={"language": "pt-br", "next": reverse("home")})
        # Then switch to en
        response = client.post(
            set_lang_url,
            data={"language": "en", "next": reverse("home")},
            follow=True,
        )
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Connecting Investors and Missionaries" in content
        assert "How It Works" in content

    def test_pages_in_both_languages(self, client):
        # Test Contact page in English
        client.cookies["django_language"] = "en"
        response_en = client.get(reverse("contact"))
        assert response_en.status_code == 200
        content_en = response_en.content.decode("utf-8")
        assert "Contact Us" in content_en
        assert "Send your message" in content_en

        # Test Contact page in Portuguese
        client.cookies["django_language"] = "pt-br"
        response_pt = client.get(reverse("contact"))
        assert response_pt.status_code == 200
        content_pt = response_pt.content.decode("utf-8")
        assert "Entrar em contato" in content_pt or "Fale Conosco" in content_pt
        assert "Envie sua mensagem" in content_pt

    def test_model_choices_translations(self):
        with translation.override("en"):
            assert BrazilianRegion.NORTE.label == "North"
            assert BrazilianRegion.NORDESTE.label == "Northeast"
            assert MissionField.Status.ASSISTED.label == "Assisted"
            assert MissionField.Status.UNASSISTED.label == "Unassisted"
            assert Adoption.Status.PENDING.label == "Pending"
            assert Adoption.Status.ACTIVE.label == "Active"
            assert TransactionType.INCOME.label == "Income"
            assert TransactionType.EXPENSE.label == "Expense"

        with translation.override("pt-br"):
            assert BrazilianRegion.NORTE.label == "Norte"
            assert BrazilianRegion.NORDESTE.label == "Nordeste"
            assert MissionField.Status.ASSISTED.label == "Assistido"
            assert MissionField.Status.UNASSISTED.label == "Não assistido"
            assert Adoption.Status.PENDING.label == "Pendente"
            assert Adoption.Status.ACTIVE.label == "Ativo"
            assert TransactionType.INCOME.label == "Receitas"
            assert TransactionType.EXPENSE.label == "Despesas"
