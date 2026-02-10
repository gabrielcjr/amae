from django.contrib import admin

from .models import Adoption, Investor, Location, Missionary, MissionField


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
    list_display = ("name", "city", "state", "is_public", "created_at")
    search_fields = ("name", "city")
    list_filter = ("state", "is_public")
    filter_horizontal = ("mission_fields",)


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "display_full_name", "created_at")
    search_fields = ("name", "city")
    list_filter = ("state", "display_full_name")


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
