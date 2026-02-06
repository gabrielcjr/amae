import datetime
from decimal import Decimal

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory

from finance.admin import TransactionAdmin
from finance.models import Transaction, TransactionType
from finance.receipt import _int_to_words, amount_to_words, generate_receipt_pdf

# --- _int_to_words ---


class TestIntToWords:
    def test_zero(self):
        assert _int_to_words(0) == "zero"

    def test_units(self):
        assert _int_to_words(1) == "um"
        assert _int_to_words(5) == "cinco"
        assert _int_to_words(9) == "nove"

    def test_teens(self):
        assert _int_to_words(10) == "dez"
        assert _int_to_words(15) == "quinze"
        assert _int_to_words(19) == "dezenove"

    def test_tens(self):
        assert _int_to_words(20) == "vinte"
        assert _int_to_words(42) == "quarenta e dois"
        assert _int_to_words(99) == "noventa e nove"

    def test_hundred_exact(self):
        assert _int_to_words(100) == "cem"

    def test_hundreds(self):
        assert _int_to_words(101) == "cento e um"
        assert _int_to_words(200) == "duzentos"
        assert _int_to_words(350) == "trezentos e cinquenta"
        assert _int_to_words(999) == "novecentos e noventa e nove"

    def test_thousands(self):
        assert _int_to_words(1000) == "mil"
        assert _int_to_words(1500) == "mil e quinhentos"
        assert _int_to_words(2000) == "dois mil"
        assert _int_to_words(10000) == "dez mil"
        assert _int_to_words(999999) == (
            "novecentos e noventa e nove mil e novecentos e noventa e nove"
        )


# --- amount_to_words ---


class TestAmountToWords:
    def test_zero(self):
        assert amount_to_words(Decimal("0.00")) == "Zero reais"

    def test_one_real(self):
        assert amount_to_words(Decimal("1.00")) == "Um real"

    def test_reais(self):
        assert amount_to_words(Decimal("200.00")) == "Duzentos reais"

    def test_centavos_only(self):
        assert amount_to_words(Decimal("0.50")) == "Cinquenta centavos"

    def test_one_centavo(self):
        assert amount_to_words(Decimal("0.01")) == "Um centavo"

    def test_reais_and_centavos(self):
        assert amount_to_words(Decimal("2.50")) == "Dois reais e cinquenta centavos"

    def test_cem_reais(self):
        assert amount_to_words(Decimal("100.00")) == "Cem reais"

    def test_large_amount(self):
        result = amount_to_words(Decimal("1500.75"))
        assert result == "Mil e quinhentos reais e setenta e cinco centavos"


# --- generate_receipt_pdf ---


class TestGenerateReceiptPdf:
    def test_returns_valid_pdf(self, income_transaction):
        buf = generate_receipt_pdf(income_transaction)
        data = buf.read()
        assert len(data) > 0
        assert data[:5] == b"%PDF-"

    def test_without_adoption(self, db, category_income):
        tx = Transaction.objects.create(
            type=TransactionType.INCOME,
            category=category_income,
            description="Doação avulsa",
            amount=Decimal("100.00"),
            date=datetime.date(2025, 3, 1),
            reference_month=3,
            reference_year=2025,
        )
        buf = generate_receipt_pdf(tx)
        assert buf.read()[:5] == b"%PDF-"


# --- TransactionAdmin custom display methods ---


class TestTransactionAdminMethods:
    @pytest.fixture(autouse=True)
    def setup_admin(self):
        self.admin = TransactionAdmin(Transaction, AdminSite())

    def test_formatted_amount_income_has_plus(self, income_transaction):
        result = self.admin.formatted_amount(income_transaction)
        assert result.startswith("+")
        assert "R$" in result

    def test_formatted_amount_expense_has_minus(self, expense_transaction):
        result = self.admin.formatted_amount(expense_transaction)
        assert result.startswith("-")

    def test_formatted_amount_br_format(self, db, category_income):
        tx = Transaction.objects.create(
            type=TransactionType.INCOME,
            category=category_income,
            description="test",
            amount=Decimal("1234.56"),
            date=datetime.date(2025, 1, 1),
            reference_month=1,
            reference_year=2025,
        )
        result = self.admin.formatted_amount(tx)
        assert "1.234,56" in result

    def test_church_name_with_adoption(self, income_transaction):
        assert self.admin.church_name(income_transaction) == "Igreja Batista Central"

    def test_church_name_without_adoption(self, expense_transaction):
        assert self.admin.church_name(expense_transaction) == "-"

    def test_missionary_name_with_adoption(self, income_transaction):
        assert self.admin.missionary_name(income_transaction) == "João Silva"

    def test_missionary_name_without_adoption(self, expense_transaction):
        assert self.admin.missionary_name(expense_transaction) == "-"

    def test_reference_format(self, income_transaction):
        assert self.admin.reference(income_transaction) == "06/2025"

    def test_receipt_link_income_has_pdf(self, income_transaction):
        html = self.admin.receipt_link(income_transaction)
        assert "href=" in html
        assert "PDF" in html

    def test_receipt_link_expense_is_dash(self, expense_transaction):
        assert self.admin.receipt_link(expense_transaction) == "-"


# --- receipt_view endpoint ---


@pytest.mark.django_db
class TestReceiptView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = RequestFactory()
        self.admin = TransactionAdmin(Transaction, AdminSite())
        self.staff = User.objects.create_superuser("admin", "a@b.com", "pass")

    def test_income_returns_pdf(self, income_transaction):
        request = self.factory.get("/")
        request.user = self.staff
        response = self.admin.receipt_view(request, income_transaction.pk)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "recibo_" in response["Content-Disposition"]

    def test_expense_returns_404(self, expense_transaction):
        from django.http import Http404

        request = self.factory.get("/")
        request.user = self.staff
        with pytest.raises(Http404):
            self.admin.receipt_view(request, expense_transaction.pk)

    def test_nonexistent_returns_404(self):
        from django.http import Http404

        request = self.factory.get("/")
        request.user = self.staff
        with pytest.raises(Http404):
            self.admin.receipt_view(request, 99999)


# --- changelist_view summary ---


@pytest.mark.django_db
class TestChangelistSummary:
    def test_summary_totals(self, client, income_transaction, expense_transaction):
        user = User.objects.create_superuser("admin", "a@b.com", "pass")
        client.force_login(user)
        response = client.get("/admin/finance/transaction/")
        summary = response.context["finance_summary"]
        assert "R$" in summary["income"]
        assert "R$" in summary["expense"]
        assert "R$" in summary["balance"]
        assert isinstance(summary["balance_positive"], bool)
