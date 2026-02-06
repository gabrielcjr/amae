from decimal import Decimal

from django.contrib import admin
from django.db.models import Sum

from .models import FinancialCategory, Transaction, TransactionType


@admin.register(FinancialCategory)
class FinancialCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'order', 'is_active')
    list_filter = ('type', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'type', 'category', 'description',
        'formatted_amount', 'church_name', 'missionary_name',
        'reference',
    )
    list_filter = (
        'type', 'category', 'reference_year', 'reference_month',
        'adoption__church', 'adoption__missionary',
    )
    search_fields = (
        'description', 'notes',
        'adoption__church__name', 'adoption__missionary__name',
    )
    date_hierarchy = 'date'
    raw_id_fields = ('adoption',)
    list_per_page = 50

    @admin.display(description='Valor')
    def formatted_amount(self, obj):
        sign = '+' if obj.type == TransactionType.INCOME else '-'
        return f'{sign} R$ {obj.amount:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @admin.display(description='Igreja')
    def church_name(self, obj):
        if obj.adoption:
            return obj.adoption.church.name
        return '-'

    @admin.display(description='Missionário')
    def missionary_name(self, obj):
        if obj.adoption:
            return obj.adoption.missionary.name
        return '-'

    @admin.display(description='Referência')
    def reference(self, obj):
        return f'{obj.reference_month:02d}/{obj.reference_year}'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        if hasattr(response, 'context_data'):
            cl = response.context_data.get('cl')
            if cl:
                queryset = cl.queryset

                income = queryset.filter(type=TransactionType.INCOME).aggregate(
                    total=Sum('amount'),
                )['total'] or Decimal('0')

                expense = queryset.filter(type=TransactionType.EXPENSE).aggregate(
                    total=Sum('amount'),
                )['total'] or Decimal('0')

                balance = income - expense

                def fmt(value):
                    return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

                response.context_data['finance_summary'] = {
                    'income': fmt(income),
                    'expense': fmt(expense),
                    'balance': fmt(balance),
                    'balance_positive': balance >= 0,
                }

        return response
