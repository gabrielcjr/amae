import json
from unittest.mock import patch

import pytest
from django.test import RequestFactory

from missions.views import missionary_detail, mission_field_map


# --- missionary_detail view ---

@pytest.mark.django_db
class TestMissionaryDetailView:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = RequestFactory()

    def _get_context(self, missionary):
        """Call view and capture the context passed to render."""
        request = self.factory.get('/')
        with patch('missions.views.render') as mock_render:
            mock_render.return_value = 'ok'
            missionary_detail(request, missionary.pk)
            return mock_render.call_args[0][2]

    def test_locations_have_float_coords(self, missionary, mission_field, location):
        missionary.mission_fields.add(mission_field)
        ctx = self._get_context(missionary)
        locations = ctx['locations']
        assert len(locations) == 1
        assert isinstance(locations[0]['lat'], float)
        assert isinstance(locations[0]['lng'], float)

    def test_locations_json_is_valid(self, missionary, mission_field, location):
        missionary.mission_fields.add(mission_field)
        ctx = self._get_context(missionary)
        data = json.loads(ctx['locations_json'])
        assert isinstance(data, list)
        assert data[0]['name'] == 'Vila Teste'

    def test_no_locations_returns_empty(self, missionary):
        ctx = self._get_context(missionary)
        assert ctx['locations'] == []


# --- mission_field_map view ---

@pytest.mark.django_db
class TestMissionFieldMapView:
    def test_fields_json_valid(self, client, mission_field, location, missionary):
        missionary.mission_fields.add(mission_field)
        response = client.get('/campos-missionarios/')
        data = json.loads(response.context['fields_json'])
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_fields_json_structure(self, client, mission_field, location, missionary):
        missionary.mission_fields.add(mission_field)
        response = client.get('/campos-missionarios/')
        data = json.loads(response.context['fields_json'])
        field = next(f for f in data if f['id'] == mission_field.pk)
        assert field['name'] == 'Campo Teste'
        assert field['region'] == 'Nordeste'
        assert field['state'] == 'BA'
        assert len(field['locations']) == 1
        assert isinstance(field['locations'][0]['lat'], float)
        assert 'João Silva' in field['missionaries']
