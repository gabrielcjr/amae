import json
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.db import IntegrityError
from django.test import RequestFactory

from missions.models import (
    Adoption,
    Investor,
    Location,
    MissionField,
    MissionFieldRequest,
)
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
        field = MissionField.objects.prefetch_related("locations", "missionaries").get(
            pk=mission_field.pk
        )
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
        response = client.get("/mission-fields/")
        data = json.loads(response.context["fields_json"])
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_fields_json_structure(self, client, mission_field, location, missionary):
        missionary.mission_fields.add(mission_field)
        response = client.get("/mission-fields/")
        data = json.loads(response.context["fields_json"])
        field = next(f for f in data if f["id"] == mission_field.pk)
        assert field["name"] == "Campo Teste"
        assert field["region"] == "Nordeste"
        assert field["state"] == "BA"
        assert len(field["locations"]) == 1
        assert isinstance(field["locations"][0]["lat"], float)
        assert "João Silva" in field["missionaries"]


# --- MissionFieldRequest model ---


@pytest.mark.django_db
class TestMissionFieldRequestModel:
    def test_pending_does_not_add_to_m2m(self, missionary, mission_field):
        MissionFieldRequest.objects.create(
            missionary=missionary,
            mission_field=mission_field,
        )
        assert not missionary.mission_fields.filter(pk=mission_field.pk).exists()

    def test_approved_adds_to_m2m(self, missionary, mission_field):
        req = MissionFieldRequest.objects.create(
            missionary=missionary,
            mission_field=mission_field,
        )
        req.status = MissionFieldRequest.Status.APPROVED
        req.save()
        assert missionary.mission_fields.filter(pk=mission_field.pk).exists()

    def test_unique_per_missionary_field_pair(self, missionary, mission_field):
        MissionFieldRequest.objects.create(
            missionary=missionary, mission_field=mission_field
        )
        with pytest.raises(IntegrityError):
            MissionFieldRequest.objects.create(
                missionary=missionary, mission_field=mission_field
            )


# --- Missionary dashboard ---


@pytest.mark.django_db
class TestMissionaryDashboardView:
    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get("/dashboard/missionary/")
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_unlinked_user_sees_unlinked_message(self, client, missionary_user):
        client.force_login(missionary_user)
        response = client.get("/dashboard/missionary/")
        assert response.status_code == 200
        assert response.context["missionary"] is None
        assert "Perfil ainda não vinculado" in response.content.decode()

    def test_linked_user_sees_dashboard(self, client, linked_missionary, mission_field):
        linked_missionary.mission_fields.add(mission_field)
        client.force_login(linked_missionary.user)
        response = client.get("/dashboard/missionary/")
        assert response.status_code == 200
        assert response.context["missionary"] == linked_missionary
        assert mission_field in list(response.context["approved_fields"])

    def test_available_excludes_approved_and_pending(
        self, client, linked_missionary, mission_field
    ):
        approved_field = mission_field
        pending_field = MissionField.objects.create(name="Pending Field")
        free_field = MissionField.objects.create(name="Free Field")

        linked_missionary.mission_fields.add(approved_field)
        MissionFieldRequest.objects.create(
            missionary=linked_missionary, mission_field=pending_field
        )

        client.force_login(linked_missionary.user)
        response = client.get("/dashboard/missionary/")
        available = list(response.context["available_fields"])
        assert approved_field not in available
        assert pending_field not in available
        assert free_field in available


@pytest.mark.django_db
class TestRequestMissionField:
    def test_creates_pending_request(self, client, linked_missionary, mission_field):
        client.force_login(linked_missionary.user)
        response = client.post(
            f"/dashboard/missionary/request-field/{mission_field.pk}/",
            {"message": "quero servir"},
        )
        assert response.status_code == 302
        req = MissionFieldRequest.objects.get(
            missionary=linked_missionary, mission_field=mission_field
        )
        assert req.status == MissionFieldRequest.Status.PENDING
        assert req.message == "quero servir"

    def test_duplicate_does_not_create_second(
        self, client, linked_missionary, mission_field
    ):
        MissionFieldRequest.objects.create(
            missionary=linked_missionary, mission_field=mission_field
        )
        client.force_login(linked_missionary.user)
        client.post(f"/dashboard/missionary/request-field/{mission_field.pk}/")
        assert (
            MissionFieldRequest.objects.filter(
                missionary=linked_missionary, mission_field=mission_field
            ).count()
            == 1
        )

    def test_unlinked_user_cannot_create(self, client, missionary_user, mission_field):
        client.force_login(missionary_user)
        client.post(f"/dashboard/missionary/request-field/{mission_field.pk}/")
        assert MissionFieldRequest.objects.count() == 0

    def test_get_not_allowed(self, client, linked_missionary, mission_field):
        client.force_login(linked_missionary.user)
        response = client.get(
            f"/dashboard/missionary/request-field/{mission_field.pk}/"
        )
        assert response.status_code == 405


@pytest.mark.django_db
class TestCancelFieldRequest:
    def test_deletes_own_pending_request(
        self, client, linked_missionary, mission_field
    ):
        req = MissionFieldRequest.objects.create(
            missionary=linked_missionary, mission_field=mission_field
        )
        client.force_login(linked_missionary.user)
        response = client.post(f"/dashboard/missionary/cancel-request/{req.pk}/")
        assert response.status_code == 302
        assert not MissionFieldRequest.objects.filter(pk=req.pk).exists()

    def test_cannot_cancel_approved_request(
        self, client, linked_missionary, mission_field
    ):
        req = MissionFieldRequest.objects.create(
            missionary=linked_missionary,
            mission_field=mission_field,
            status=MissionFieldRequest.Status.APPROVED,
        )
        client.force_login(linked_missionary.user)
        response = client.post(f"/dashboard/missionary/cancel-request/{req.pk}/")
        assert response.status_code == 404
        assert MissionFieldRequest.objects.filter(pk=req.pk).exists()

    def test_cannot_cancel_other_users_request(
        self, client, linked_missionary, mission_field
    ):
        from django.contrib.auth.models import User

        req = MissionFieldRequest.objects.create(
            missionary=linked_missionary, mission_field=mission_field
        )
        intruder = User.objects.create_user(username="intruder@test.com", password="x")
        client.force_login(intruder)
        response = client.post(f"/dashboard/missionary/cancel-request/{req.pk}/")
        assert response.status_code == 302
        assert MissionFieldRequest.objects.filter(pk=req.pk).exists()


# --- Investor dashboard ---


@pytest.mark.django_db
class TestInvestorDashboardView:
    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get("/dashboard/investor/")
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_unlinked_user_sees_unlinked_message(self, client, investor_user):
        client.force_login(investor_user)
        response = client.get("/dashboard/investor/")
        assert response.status_code == 200
        assert response.context["investor"] is None
        assert "Perfil ainda não vinculado" in response.content.decode()

    def test_linked_user_dashboard_shows_active_total(
        self, client, linked_investor, missionary, mission_field
    ):
        import datetime as _dt

        Adoption.objects.create(
            investor=linked_investor,
            missionary=missionary,
            mission_field=mission_field,
            monthly_value=Decimal("250.00"),
            start_date=_dt.date(2025, 1, 1),
            status=Adoption.Status.ACTIVE,
        )
        client.force_login(linked_investor.user)
        response = client.get("/dashboard/investor/")
        assert response.status_code == 200
        assert response.context["total_monthly"] == Decimal("250.00")
        assert len(response.context["active_adoptions"]) == 1


@pytest.mark.django_db
class TestRequestAdoption:
    def test_creates_pending_adoption(
        self, client, linked_investor, missionary, mission_field
    ):
        missionary.mission_fields.add(mission_field)
        client.force_login(linked_investor.user)
        response = client.post(
            "/dashboard/investor/request-adoption/",
            {
                "missionary_id": missionary.pk,
                "mission_field_id": mission_field.pk,
                "monthly_value": "100.50",
            },
        )
        assert response.status_code == 302
        adoption = Adoption.objects.get(investor=linked_investor, missionary=missionary)
        assert adoption.status == Adoption.Status.PENDING
        assert adoption.monthly_value == Decimal("100.50")

    def test_rejects_field_not_in_missionary(
        self, client, linked_investor, missionary, mission_field
    ):
        # Don't add field to missionary's mission_fields
        client.force_login(linked_investor.user)
        client.post(
            "/dashboard/investor/request-adoption/",
            {
                "missionary_id": missionary.pk,
                "mission_field_id": mission_field.pk,
                "monthly_value": "100",
            },
        )
        assert (
            Adoption.objects.filter(
                investor=linked_investor, missionary=missionary
            ).count()
            == 0
        )

    def test_rejects_invalid_monthly_value(
        self, client, linked_investor, missionary, mission_field
    ):
        missionary.mission_fields.add(mission_field)
        client.force_login(linked_investor.user)
        client.post(
            "/dashboard/investor/request-adoption/",
            {
                "missionary_id": missionary.pk,
                "mission_field_id": mission_field.pk,
                "monthly_value": "abc",
            },
        )
        assert Adoption.objects.filter(investor=linked_investor).count() == 0

    def test_rejects_non_positive_value(
        self, client, linked_investor, missionary, mission_field
    ):
        missionary.mission_fields.add(mission_field)
        client.force_login(linked_investor.user)
        client.post(
            "/dashboard/investor/request-adoption/",
            {
                "missionary_id": missionary.pk,
                "mission_field_id": mission_field.pk,
                "monthly_value": "0",
            },
        )
        assert Adoption.objects.filter(investor=linked_investor).count() == 0

    def test_rejects_duplicate_pending(
        self, client, linked_investor, missionary, mission_field
    ):
        import datetime as _dt

        missionary.mission_fields.add(mission_field)
        Adoption.objects.create(
            investor=linked_investor,
            missionary=missionary,
            mission_field=mission_field,
            monthly_value=Decimal("100"),
            start_date=_dt.date(2025, 1, 1),
            status=Adoption.Status.PENDING,
        )
        client.force_login(linked_investor.user)
        client.post(
            "/dashboard/investor/request-adoption/",
            {
                "missionary_id": missionary.pk,
                "mission_field_id": mission_field.pk,
                "monthly_value": "200",
            },
        )
        assert (
            Adoption.objects.filter(
                investor=linked_investor,
                missionary=missionary,
                mission_field=mission_field,
            ).count()
            == 1
        )

    def test_unlinked_user_cannot_create(
        self, client, investor_user, missionary, mission_field
    ):
        missionary.mission_fields.add(mission_field)
        client.force_login(investor_user)
        client.post(
            "/dashboard/investor/request-adoption/",
            {
                "missionary_id": missionary.pk,
                "mission_field_id": mission_field.pk,
                "monthly_value": "100",
            },
        )
        assert Adoption.objects.count() == 0


@pytest.mark.django_db
class TestCancelAdoptionRequest:
    def test_deletes_own_pending(
        self, client, linked_investor, missionary, mission_field
    ):
        import datetime as _dt

        adoption = Adoption.objects.create(
            investor=linked_investor,
            missionary=missionary,
            mission_field=mission_field,
            monthly_value=Decimal("100"),
            start_date=_dt.date(2025, 1, 1),
            status=Adoption.Status.PENDING,
        )
        client.force_login(linked_investor.user)
        response = client.post(f"/dashboard/investor/cancel-adoption/{adoption.pk}/")
        assert response.status_code == 302
        assert not Adoption.objects.filter(pk=adoption.pk).exists()

    def test_cannot_cancel_active(
        self, client, linked_investor, missionary, mission_field
    ):
        import datetime as _dt

        adoption = Adoption.objects.create(
            investor=linked_investor,
            missionary=missionary,
            mission_field=mission_field,
            monthly_value=Decimal("100"),
            start_date=_dt.date(2025, 1, 1),
            status=Adoption.Status.ACTIVE,
        )
        client.force_login(linked_investor.user)
        response = client.post(f"/dashboard/investor/cancel-adoption/{adoption.pk}/")
        assert response.status_code == 404
        assert Adoption.objects.filter(pk=adoption.pk).exists()


# --- dashboard_redirect ---


@pytest.mark.django_db
class TestDashboardRedirect:
    def test_missionary_user_goes_to_missionary_dashboard(
        self, client, linked_missionary
    ):
        client.force_login(linked_missionary.user)
        response = client.get("/dashboard/")
        assert response.status_code == 302
        assert response.url == "/dashboard/missionary/"

    def test_investor_user_goes_to_investor_dashboard(self, client, linked_investor):
        client.force_login(linked_investor.user)
        response = client.get("/dashboard/")
        assert response.status_code == 302
        assert response.url == "/dashboard/investor/"

    def test_unlinked_user_goes_to_mission_fields(self, client, missionary_user):
        client.force_login(missionary_user)
        response = client.get("/dashboard/")
        assert response.status_code == 302
        assert response.url == "/mission-fields/"

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get("/dashboard/")
        assert response.status_code == 302
        assert "/login/" in response.url


# --- MissionField status & reactive calculation tests ---


@pytest.mark.django_db
class TestMissionFieldStatusCalculation:
    def test_initial_creation_calculates_status(self):
        field = MissionField.objects.create(name="Novo Campo", missionaries_needed=1)
        assert field.status == MissionField.Status.UNASSISTED

    def test_initial_creation_needed_zero_is_assisted(self):
        field = MissionField.objects.create(name="Campo Zero", missionaries_needed=0)
        assert field.status == MissionField.Status.ASSISTED

    def test_count_includes_adoption_field_without_m2m(
        self, missionary, investor, mission_field
    ):
        # missionary is NOT added to mission_field.missionaries M2M
        import datetime as _dt

        assert mission_field.get_current_missionaries_count() == 0
        Adoption.objects.create(
            missionary=missionary,
            investor=investor,
            mission_field=mission_field,
            monthly_value=Decimal("500.00"),
            start_date=_dt.date(2025, 1, 1),
            status=Adoption.Status.ACTIVE,
        )
        assert mission_field.get_current_missionaries_count() == 1

    def test_adoption_status_change_updates_mission_field_status(
        self, missionary, investor, mission_field
    ):
        import datetime as _dt

        field = MissionField.objects.create(name="Campo Status", missionaries_needed=1)
        assert field.status == MissionField.Status.UNASSISTED

        adoption = Adoption.objects.create(
            missionary=missionary,
            investor=investor,
            mission_field=field,
            monthly_value=Decimal("500.00"),
            start_date=_dt.date(2025, 1, 1),
            status=Adoption.Status.PENDING,
        )
        field.refresh_from_db()
        assert field.status == MissionField.Status.UNASSISTED

        adoption.status = Adoption.Status.ACTIVE
        adoption.save()
        field.refresh_from_db()
        assert field.status == MissionField.Status.ASSISTED

        adoption.status = Adoption.Status.CANCELLED
        adoption.save()
        field.refresh_from_db()
        assert field.status == MissionField.Status.UNASSISTED

    def test_adoption_delete_updates_mission_field_status(self, missionary, investor):
        import datetime as _dt

        field = MissionField.objects.create(name="Campo Delete", missionaries_needed=1)
        adoption = Adoption.objects.create(
            missionary=missionary,
            investor=investor,
            mission_field=field,
            monthly_value=Decimal("500.00"),
            start_date=_dt.date(2025, 1, 1),
            status=Adoption.Status.ACTIVE,
        )
        field.refresh_from_db()
        assert field.status == MissionField.Status.ASSISTED

        adoption.delete()
        field.refresh_from_db()
        assert field.status == MissionField.Status.UNASSISTED


@pytest.mark.django_db
class TestAdoptionAdminActions:
    def test_approve_adoptions_action_updates_status(self, missionary, investor):
        import datetime as _dt
        from unittest.mock import patch

        from django.contrib.admin.sites import AdminSite

        from missions.admin import AdoptionAdmin

        field = MissionField.objects.create(name="Campo Admin", missionaries_needed=1)
        adoption = Adoption.objects.create(
            missionary=missionary,
            investor=investor,
            mission_field=field,
            monthly_value=Decimal("500.00"),
            start_date=_dt.date(2025, 1, 1),
            status=Adoption.Status.PENDING,
        )

        admin = AdoptionAdmin(Adoption, AdminSite())
        rf = RequestFactory()
        request = rf.get("/")
        with patch.object(admin, "message_user"):
            admin.approve_adoptions(request, Adoption.objects.filter(pk=adoption.pk))

        adoption.refresh_from_db()
        assert adoption.status == Adoption.Status.ACTIVE
        field.refresh_from_db()
        assert field.status == MissionField.Status.ASSISTED


@pytest.mark.django_db
class TestInvestorDetailView:
    def test_unauthenticated_user_sees_masked_name_and_no_contact_info(
        self, client, investor
    ):
        investor.display_full_name = False
        investor.contact_email = "secret@test.com"
        investor.contact_phone = "11999999999"
        investor.save()

        response = client.get(f"/investors/{investor.pk}/")
        assert response.status_code == 200
        content = response.content.decode()
        assert investor.get_display_name() in content
        assert "secret@test.com" not in content
        assert "11999999999" not in content

    def test_owner_user_sees_contact_info(self, client, linked_investor):
        linked_investor.contact_email = "owner@test.com"
        linked_investor.save()

        client.force_login(linked_investor.user)
        response = client.get(f"/investors/{linked_investor.pk}/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "owner@test.com" in content
