import json

from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .models import Investor, Missionary, MissionField


def _serialize_location(location):
    return {
        "name": location.name,
        "lat": float(location.latitude),
        "lng": float(location.longitude),
    }


def _serialize_locations(mission_fields):
    return [
        _serialize_location(location)
        for field in mission_fields
        for location in field.locations.all()
    ]


def _serialize_mission_field(field):
    return {
        "id": field.pk,
        "name": field.name,
        "description": field.description,
        "region": field.region,
        "state": field.state,
        "status": field.status,
        "missionaries": [m.name for m in field.missionaries.all()],
        "locations": [_serialize_location(location) for location in field.locations.all()],
    }


def home(request):
    return render(request, "home.html")


def missionary_list(request):
    missionaries = Missionary.objects.filter(is_public=True).prefetch_related(
        "mission_fields"
    )
    return render(
        request,
        "missions/missionary_list.html",
        {
            "missionaries": missionaries,
        },
    )


def missionary_detail(request, pk):
    missionary = get_object_or_404(
        Missionary.objects.prefetch_related("mission_fields", "adoptions__investor"),
        pk=pk,
    )
    adoptions = missionary.adoptions.select_related("investor").all()
    fields = missionary.mission_fields.prefetch_related("locations").all()
    locations = _serialize_locations(fields)

    return render(
        request,
        "missions/missionary_detail.html",
        {
            "missionary": missionary,
            "adoptions": adoptions,
            "locations": locations,
            "locations_json": json.dumps(locations),
            "google_maps_api_key": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
        },
    )


def mission_field_map(request):
    mission_fields = MissionField.objects.prefetch_related(
        "locations", "missionaries"
    ).all()

    fields_data = [_serialize_mission_field(field) for field in mission_fields]

    return render(
        request,
        "missions/mission_field_map.html",
        {
            "mission_fields": mission_fields,
            "fields_json": json.dumps(fields_data),
            "google_maps_api_key": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
        },
    )


def investor_detail(request, pk):
    investor = get_object_or_404(Investor, pk=pk)
    adoptions = investor.adoptions.select_related("missionary").all()
    return render(
        request,
        "missions/investor_detail.html",
        {
            "investor": investor,
            "adoptions": adoptions,
        },
    )
