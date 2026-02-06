from django.db import models


class TransactionType(models.TextChoices):
    INCOME = "income", "Receita"
    EXPENSE = "expense", "Despesa"


class FinancialCategory(models.Model):
    name = models.CharField("Nome", max_length=200)
    type = models.CharField(
        "Tipo",
        max_length=10,
        choices=TransactionType.choices,
    )
    order = models.PositiveIntegerField("Ordem", default=0)
    is_active = models.BooleanField("Ativa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["type", "order"]
        verbose_name = "Categoria Financeira"
        verbose_name_plural = "Categorias Financeiras"

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):
    type = models.CharField(
        "Tipo",
        max_length=10,
        choices=TransactionType.choices,
    )
    category = models.ForeignKey(
        FinancialCategory,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Categoria",
    )
    adoption = models.ForeignKey(
        "missions.Adoption",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        verbose_name="Adoção",
    )
    description = models.CharField("Descrição", max_length=300)
    amount = models.DecimalField(
        "Valor (R$)",
        max_digits=10,
        decimal_places=2,
    )
    date = models.DateField("Data")
    reference_month = models.PositiveIntegerField("Mês de referência")
    reference_year = models.PositiveIntegerField("Ano de referência")
    notes = models.TextField("Observações", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Transação"
        verbose_name_plural = "Transações"

    def __str__(self):
        return f"{self.get_type_display()} - {self.description} - R$ {self.amount}"
