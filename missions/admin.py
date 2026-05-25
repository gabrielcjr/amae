from django.contrib import admin, messages
from django.utils import timezone

from .models import (
    Adoption,
    Investor,
    Location,
    Missionary,
    MissionField,
    MissionFieldRequest,
)


class LocationInline(admin.TabularInline):
    model = Location
    extra = 1
    min_num = 1
    validate_min = True


@admin.register(MissionField)
class MissionFieldAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "country",
        "region",
        "state",
        "missionaries_needed",
        "current_missionaries",
        "status",
        "created_at",
    )
    search_fields = ("name",)
    list_filter = ("country", "state", "region", "status")
    readonly_fields = ("status",)
    inlines = [LocationInline]

    @admin.display(description="Missionários Atuais")
    def current_missionaries(self, obj):
        current = obj.get_current_missionaries_count()
        needed = obj.missionaries_needed
        percentage = (current / needed * 100) if needed > 0 else 0
        color = "green" if current >= needed else "orange" if current > 0 else "red"
        return f'<span style="color: {color}; font-weight: bold;">{current}/{needed} ({percentage:.0f}%)</span>'

    current_missionaries.allow_tags = True

    class Media:
        js = ("js/mission_field_country.js",)


@admin.register(Missionary)
class MissionaryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "city", "state", "is_public", "created_at")
    search_fields = ("name", "city", "user__username", "user__email")
    list_filter = ("state", "is_public")
    filter_horizontal = ("mission_fields",)
    raw_id_fields = ("user",)


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "city", "state", "display_full_name", "created_at")
    search_fields = ("name", "city", "user__username", "user__email")
    list_filter = ("state", "display_full_name")
    raw_id_fields = ("user",)


@admin.register(MissionFieldRequest)
class MissionFieldRequestAdmin(admin.ModelAdmin):
    list_display = (
        "missionary",
        "mission_field",
        "status",
        "created_at",
        "reviewed_at",
        "reviewed_by",
    )
    list_filter = ("status", "mission_field")
    search_fields = ("missionary__name", "mission_field__name")
    raw_id_fields = ("missionary", "mission_field", "reviewed_by")
    readonly_fields = ("created_at", "reviewed_at", "reviewed_by")
    actions = ("approve_requests", "reject_requests")

    @admin.action(description="Aprovar solicitações selecionadas")
    def approve_requests(self, request, queryset):
        # Save per-row (not bulk update) so MissionFieldRequest.save() runs
        # and adds the mission field to the missionary's M2M.
        pending = queryset.filter(status=MissionFieldRequest.Status.PENDING)
        count = 0
        for req in pending:
            req.status = MissionFieldRequest.Status.APPROVED
            req.reviewed_at = timezone.now()
            req.reviewed_by = request.user
            req.save()
            count += 1
        self.message_user(
            request, f"{count} solicitação(ões) aprovada(s).", messages.SUCCESS
        )

    @admin.action(description="Rejeitar solicitações selecionadas")
    def reject_requests(self, request, queryset):
        pending = queryset.filter(status=MissionFieldRequest.Status.PENDING)
        count = pending.update(
            status=MissionFieldRequest.Status.REJECTED,
            reviewed_at=timezone.now(),
            reviewed_by=request.user,
        )
        self.message_user(
            request, f"{count} solicitação(ões) rejeitada(s).", messages.SUCCESS
        )


@admin.register(Adoption)
class AdoptionAdmin(admin.ModelAdmin):
    list_display = (
        "investor",
        "missionary",
        "mission_field",
        "monthly_value",
        "status",
        "start_date",
        "end_date",
    )
    list_filter = ("status", "mission_field")
    search_fields = ("investor__name", "missionary__name")
    raw_id_fields = ("investor", "missionary")
    actions = ("approve_adoptions", "reject_adoptions")

    @admin.action(description="Aprovar adoções selecionadas")
    def approve_adoptions(self, request, queryset):
        count = queryset.filter(status=Adoption.Status.PENDING).update(
            status=Adoption.Status.ACTIVE
        )
        self.message_user(
            request, f"{count} adoção(ões) aprovada(s).", messages.SUCCESS
        )

    @admin.action(description="Rejeitar adoções selecionadas")
    def reject_adoptions(self, request, queryset):
        count = queryset.filter(status=Adoption.Status.PENDING).update(
            status=Adoption.Status.CANCELLED
        )
        self.message_user(
            request, f"{count} adoção(ões) rejeitada(s).", messages.SUCCESS
        )
