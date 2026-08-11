import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from finance.models import FinancialCategory, Transaction, TransactionType
from missions.models import Adoption, Investor, Location, Missionary, MissionField


@pytest.fixture
def mission_field(db):
    return MissionField.objects.create(
        name="Campo Teste",
        state="BA",
        region="Nordeste",
        population=5000,
    )


@pytest.fixture
def location(db, mission_field):
    return Location.objects.create(
        mission_field=mission_field,
        name="Vila Teste",
        latitude=Decimal("-12.971"),
        longitude=Decimal("-38.511"),
    )


@pytest.fixture
def missionary(db):
    return Missionary.objects.create(
        name="João Silva",
        city="Salvador",
        state="BA",
        is_public=True,
    )


@pytest.fixture
def investor(db):
    return Investor.objects.create(
        name="João Silva Investidor",
        city="São Paulo",
        state="SP",
        contact_email="contato@investidor.com",
    )


@pytest.fixture
def missionary_user(db):
    return User.objects.create_user(
        username="missionary@test.com",
        email="missionary@test.com",
        password="testpass123",
    )


@pytest.fixture
def investor_user(db):
    return User.objects.create_user(
        username="investor@test.com",
        email="investor@test.com",
        password="testpass123",
    )


@pytest.fixture
def linked_missionary(missionary, missionary_user):
    missionary.user = missionary_user
    missionary.save()
    return missionary


@pytest.fixture
def linked_investor(investor, investor_user):
    investor.user = investor_user
    investor.save()
    return investor


@pytest.fixture
def adoption(db, missionary, investor, mission_field):
    return Adoption.objects.create(
        missionary=missionary,
        investor=investor,
        mission_field=mission_field,
        monthly_value=Decimal("500.00"),
        start_date=datetime.date(2025, 1, 1),
    )


@pytest.fixture
def category_income(db):
    return FinancialCategory.objects.create(
        name="Ofertas",
        type=TransactionType.INCOME,
    )


@pytest.fixture
def category_expense(db):
    return FinancialCategory.objects.create(
        name="Aluguel",
        type=TransactionType.EXPENSE,
    )


@pytest.fixture
def income_transaction(db, category_income, adoption):
    return Transaction.objects.create(
        type=TransactionType.INCOME,
        category=category_income,
        adoption=adoption,
        description="Oferta mensal",
        amount=Decimal("500.00"),
        date=datetime.date(2025, 6, 15),
        reference_month=6,
        reference_year=2025,
    )


@pytest.fixture
def expense_transaction(db, category_expense):
    return Transaction.objects.create(
        type=TransactionType.EXPENSE,
        category=category_expense,
        description="Aluguel sede",
        amount=Decimal("1200.00"),
        date=datetime.date(2025, 6, 10),
        reference_month=6,
        reference_year=2025,
    )
