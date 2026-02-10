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
        "population",
        "status",
        "created_at",
    )
    search_fields = ("name",)
    list_filter = ("country", "state", "region", "status")
    inlines = [LocationInline]

    class Media:
        js = ("js/mission_field_country.js",)


@admin.register(Missionary)
class MissionaryAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "created_at")
    search_fields = ("name", "city")
    list_filter = ("state",)
    filter_horizontal = ("mission_fields",)


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "created_at")
    search_fields = ("name", "city")
    list_filter = ("state",)


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
