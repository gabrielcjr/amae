import json
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.test import RequestFactory

from missions.models import Investor, Location, MissionField
from missions.views import (
    _serialize_location,
    _serialize_locations,
    _serialize_mission_field,
    missionary_detail,
)

# --- _serialize_location ---


@pytest.mark.django_db
class TestSerializeLocation:
    def test_returns_correct_structure(self, location):
        result = _serialize_location(location)
        assert result == {
            "name": "Vila Teste",
            "lat": float(location.latitude),
            "lng": float(location.longitude),
        }

    def test_coords_are_floats(self, location):
        result = _serialize_location(location)
        assert isinstance(result["lat"], float)
        assert isinstance(result["lng"], float)


# --- _serialize_locations ---


@pytest.mark.django_db
class TestSerializeLocations:
    def test_serializes_all_locations(self, mission_field, location):
        Location.objects.create(
            mission_field=mission_field,
            name="Vila Dois",
            latitude=Decimal("-13.000"),
            longitude=Decimal("-39.000"),
        )
        fields = MissionField.objects.prefetch_related("locations").filter(
            pk=mission_field.pk
        )
        result = _serialize_locations(fields)
        assert len(result) == 2
        names = {loc["name"] for loc in result}
        assert "Vila Teste" in names
        assert "Vila Dois" in names

    def test_empty_fields(self, db):
        result = _serialize_locations([])
        assert result == []


# --- _serialize_mission_field ---


@pytest.mark.django_db
class TestSerializeMissionField:
    def test_returns_correct_structure(self, mission_field, location, missionary):
        missionary.mission_fields.add(mission_field)
        field = MissionField.objects.prefetch_related(
            "locations", "missionaries"
        ).get(pk=mission_field.pk)
        result = _serialize_mission_field(field)
        assert result["id"] == mission_field.pk
        assert result["name"] == "Campo Teste"
        assert result["region"] == "Nordeste"
        assert result["state"] == "BA"
        assert len(result["locations"]) == 1
        assert "João Silva" in result["missionaries"]


# --- Investor.get_display_name ---


@pytest.mark.django_db
class TestInvestorGetDisplayName:
    def test_full_name_when_enabled(self):
        investor = Investor.objects.create(
            name="Maria Santos",
            city="SP",
            state="SP",
            display_full_name=True,
        )
        assert investor.get_display_name() == "Maria Santos"

    def test_masked_name_when_disabled(self):
        investor = Investor.objects.create(
            name="Maria Santos",
            city="SP",
            state="SP",
            display_full_name=False,
        )
        assert investor.get_display_name() == "M...s"

    def test_single_char_name(self):
        investor = Investor.objects.create(
            name="M",
            city="SP",
            state="SP",
            display_full_name=False,
        )
        assert investor.get_display_name() == "M"

    def test_empty_name(self):
        investor = Investor.objects.create(
            name="",
            city="SP",
            state="SP",
            display_full_name=False,
        )
        assert investor.get_display_name() == ""

    def test_two_char_name(self):
        investor = Investor.objects.create(
            name="AB",
            city="SP",
            state="SP",
            display_full_name=False,
        )
        assert investor.get_display_name() == "A...B"


# --- missionary_detail view ---


@pytest.mark.django_db
class TestMissionaryDetailView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = RequestFactory()

    def _get_context(self, missionary):
        """Call view and capture the context passed to render."""
        request = self.factory.get("/")
        with patch("missions.views.render") as mock_render:
            mock_render.return_value = "ok"
            missionary_detail(request, missionary.pk)
            return mock_render.call_args[0][2]

    def test_locations_have_float_coords(self, missionary, mission_field, location):
        missionary.mission_fields.add(mission_field)
        ctx = self._get_context(missionary)
        locations = ctx["locations"]
        assert len(locations) == 1
        assert isinstance(locations[0]["lat"], float)
        assert isinstance(locations[0]["lng"], float)

    def test_locations_json_is_valid(self, missionary, mission_field, location):
        missionary.mission_fields.add(mission_field)
        ctx = self._get_context(missionary)
        data = json.loads(ctx["locations_json"])
        assert isinstance(data, list)
        assert data[0]["name"] == "Vila Teste"

    def test_no_locations_returns_empty(self, missionary):
        ctx = self._get_context(missionary)
        assert ctx["locations"] == []


# --- mission_field_map view ---


@pytest.mark.django_db
class TestMissionFieldMapView:
    def test_fields_json_valid(self, client, mission_field, location, missionary):
        missionary.mission_fields.add(mission_field)
        response = client.get("/campos-missionarios/")
        data = json.loads(response.context["fields_json"])
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_fields_json_structure(self, client, mission_field, location, missionary):
        missionary.mission_fields.add(mission_field)
        response = client.get("/campos-missionarios/")
        data = json.loads(response.context["fields_json"])
        field = next(f for f in data if f["id"] == mission_field.pk)
        assert field["name"] == "Campo Teste"
        assert field["region"] == "Nordeste"
        assert field["state"] == "BA"
        assert len(field["locations"]) == 1
        assert isinstance(field["locations"][0]["lat"], float)
        assert "João Silva" in field["missionaries"]
