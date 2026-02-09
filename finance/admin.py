from datetime import date
from decimal import Decimal

from django.contrib import admin
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import FinancialCategory, Transaction, TransactionType
from .receipt import MONTHS_PT


@admin.register(FinancialCategory)
class FinancialCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "order", "is_active")
    list_filter = ("type", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "type",
        "category",
        "description",
        "formatted_amount",
        "church_name",
        "missionary_name",
        "reference",
        "receipt_link",
    )
    list_filter = (
        "type",
        "category",
        "reference_year",
        "reference_month",
        "adoption__church",
        "adoption__missionary",
    )
    search_fields = (
        "description",
        "notes",
        "adoption__church__name",
        "adoption__missionary__name",
    )
    date_hierarchy = "date"
    raw_id_fields = ("adoption",)
    list_per_page = 50
    list_select_related = (
        "category",
        "adoption__church",
        "adoption__missionary",
        "adoption__mission_field",
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/receipt/",
                self.admin_site.admin_view(self.receipt_view),
                name="finance_transaction_receipt",
            ),
            path(
                "report/",
                self.admin_site.admin_view(self.report_view),
                name="finance_transaction_report",
            ),
            path(
                "general-report/",
                self.admin_site.admin_view(self.general_report_view),
                name="finance_transaction_general_report",
            ),
        ]
        return custom_urls + urls

    def receipt_view(self, request, pk):
        from .receipt import generate_receipt_pdf

        try:
            transaction = Transaction.objects.select_related(
                "adoption__church",
            ).get(pk=pk, type=TransactionType.INCOME)
        except Transaction.DoesNotExist:
            raise Http404

        pdf = generate_receipt_pdf(transaction)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="recibo_{pk}.pdf"'
        return response

    def report_view(self, request):
        cl = self.get_changelist_instance(request)
        queryset = cl.queryset.select_related(
            "category", "adoption__church", "adoption__missionary"
        )

        income = queryset.filter(type=TransactionType.INCOME).aggregate(
            total=Sum("amount"),
        )["total"] or Decimal("0")
        expense = queryset.filter(type=TransactionType.EXPENSE).aggregate(
            total=Sum("amount"),
        )["total"] or Decimal("0")
        balance = income - expense

        def fmt(value):
            return (
                f"R$ {value:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        # Add formatted amount to each transaction for the template
        transactions = list(queryset)
        for tx in transactions:
            sign = "+" if tx.type == TransactionType.INCOME else "-"
            tx.formatted_amount = (
                f"{sign} R$ {tx.amount:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

        today = date.today()
        footer_text = (
            f"Relatório gerado em {today.day:02d} de "
            f"{MONTHS_PT[today.month]} de {today.year}"
        )

        context = {
            "transactions": transactions,
            "income": fmt(income),
            "expense": fmt(expense),
            "balance": fmt(balance),
            "balance_positive": balance >= 0,
            "filters_description": self._build_filters_description(request),
            "footer_text": footer_text,
        }
        return TemplateResponse(
            request,
            "admin/finance/transaction/report.html",
            context,
        )

    def general_report_view(self, request):
        from .report import generate_general_report_pdf

        cl = self.get_changelist_instance(request)
        queryset = cl.queryset

        expense = queryset.filter(type=TransactionType.EXPENSE).aggregate(
            total=Sum("amount"),
        )["total"] or Decimal("0")

        filters = self._build_filters_description(request)
        pdf = generate_general_report_pdf(queryset, expense, filters)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="relatorio_geral.pdf"'
        return response

    def _build_filters_description(self, request):
        parts = []
        params = request.GET

        if params.get("type__exact"):
            label = "Receita" if params["type__exact"] == "income" else "Despesa"
            parts.append(f"Tipo: {label}")
        if params.get("reference_year__exact"):
            parts.append(f"Ano: {params['reference_year__exact']}")
        if params.get("reference_month__exact"):
            parts.append(f"Mês: {params['reference_month__exact']}")
        if params.get("adoption__church__id__exact"):
            from missions.models import Church

            try:
                church = Church.objects.get(pk=params["adoption__church__id__exact"])
                parts.append(f"Igreja: {church.name}")
            except Church.DoesNotExist:
                pass
        if params.get("adoption__missionary__id__exact"):
            from missions.models import Missionary

            try:
                missionary = Missionary.objects.get(
                    pk=params["adoption__missionary__id__exact"]
                )
                parts.append(f"Missionário: {missionary.name}")
            except Missionary.DoesNotExist:
                pass

        return " | ".join(parts) if parts else "Todas as transações"

    @admin.display(description="Recibo")
    def receipt_link(self, obj):
        if obj.type == TransactionType.INCOME:
            url = reverse("admin:finance_transaction_receipt", args=[obj.pk])
            return format_html('<a href="{}">PDF</a>', url)
        return "-"

    @admin.display(description="Valor")
    def formatted_amount(self, obj):
        sign = "+" if obj.type == TransactionType.INCOME else "-"
        return (
            f"{sign} R$ {obj.amount:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    @admin.display(description="Igreja")
    def church_name(self, obj):
        if obj.adoption:
            return obj.adoption.church.name
        return "-"

    @admin.display(description="Missionário")
    def missionary_name(self, obj):
        if obj.adoption:
            return obj.adoption.missionary.name
        return "-"

    @admin.display(description="Referência")
    def reference(self, obj):
        return f"{obj.reference_month:02d}/{obj.reference_year}"

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, "context_data"):
            cl = response.context_data.get("cl")
            if cl:
                queryset = cl.queryset

                income = queryset.filter(type=TransactionType.INCOME).aggregate(
                    total=Sum("amount"),
                )["total"] or Decimal("0")

                expense = queryset.filter(type=TransactionType.EXPENSE).aggregate(
                    total=Sum("amount"),
                )["total"] or Decimal("0")

                balance = income - expense

                def fmt(value):
                    return (
                        f"R$ {value:,.2f}".replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )

                response.context_data["finance_summary"] = {
                    "income": fmt(income),
                    "expense": fmt(expense),
                    "balance": fmt(balance),
                    "balance_positive": balance >= 0,
                }

        return response
