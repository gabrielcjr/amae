import datetime
from decimal import Decimal

import pytest

from finance.models import FinancialCategory, Transaction, TransactionType
from missions.models import Adoption, Church, Location, Missionary, MissionField


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
    )


@pytest.fixture
def church(db):
    return Church.objects.create(
        name="Igreja Batista Central",
        city="São Paulo",
        state="SP",
        contact_email="contato@ibc.org",
    )


@pytest.fixture
def adoption(db, missionary, church, mission_field):
    return Adoption.objects.create(
        missionary=missionary,
        church=church,
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
