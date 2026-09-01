from django.db import models
from django.utils.translation import gettext_lazy as _


class TransactionType(models.TextChoices):
    INCOME = "income", _("Income")
    EXPENSE = "expense", _("Expense")


class FinancialCategory(models.Model):
    name = models.CharField(_("Name"), max_length=200)
    type = models.CharField(
        _("Type"),
        max_length=10,
        choices=TransactionType.choices,
    )
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["type", "order"]
        verbose_name = _("Financial Category")
        verbose_name_plural = _("Financial Categories")

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):
    type = models.CharField(
        _("Type"),
        max_length=10,
        choices=TransactionType.choices,
    )
    category = models.ForeignKey(
        FinancialCategory,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name=_("Category"),
    )
    adoption = models.ForeignKey(
        "missions.Adoption",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        verbose_name=_("Adoption"),
    )
    description = models.CharField(_("Description"), max_length=300)
    amount = models.DecimalField(
        _("Amount (R$)"),
        max_digits=10,
        decimal_places=2,
    )
    date = models.DateField(_("Date"))
    reference_month = models.PositiveIntegerField(_("Reference month"))
    reference_year = models.PositiveIntegerField(_("Reference year"))
    notes = models.TextField(_("Notes"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")

    def __str__(self):
        return f"{self.get_type_display()} - {self.description} - R$ {self.amount}"
