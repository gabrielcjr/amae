import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    Adoption,
    Investor,
    Missionary,
    MissionField,
    MissionFieldRequest,
)


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
        "locations": [
            _serialize_location(location) for location in field.locations.all()
        ],
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


@login_required
def dashboard_redirect(request):
    if getattr(request.user, "missionary_profile", None):
        return redirect("missionary_dashboard")
    if getattr(request.user, "investor_profile", None):
        return redirect("investor_dashboard")
    return redirect("mission_field_map")


@login_required
def missionary_dashboard(request):
    missionary = getattr(request.user, "missionary_profile", None)

    if missionary is None:
        return render(
            request,
            "missions/missionary_dashboard.html",
            {"missionary": None},
        )

    approved_fields = missionary.mission_fields.prefetch_related("locations").all()
    requests_qs = missionary.field_requests.select_related("mission_field").all()
    pending_requests = [
        r for r in requests_qs if r.status == MissionFieldRequest.Status.PENDING
    ]
    rejected_requests = [
        r for r in requests_qs if r.status == MissionFieldRequest.Status.REJECTED
    ]

    taken_field_ids = set(approved_fields.values_list("pk", flat=True))
    taken_field_ids.update(r.mission_field_id for r in pending_requests)

    available_fields = (
        MissionField.objects.exclude(pk__in=taken_field_ids)
        .prefetch_related("locations")
        .order_by("name")
    )

    return render(
        request,
        "missions/missionary_dashboard.html",
        {
            "missionary": missionary,
            "approved_fields": approved_fields,
            "pending_requests": pending_requests,
            "rejected_requests": rejected_requests,
            "available_fields": available_fields,
        },
    )


@login_required
@require_POST
def request_mission_field(request, field_id):
    missionary = getattr(request.user, "missionary_profile", None)
    if missionary is None:
        messages.error(request, "Seu perfil de missionário ainda não foi vinculado.")
        return redirect("missionary_dashboard")

    field = get_object_or_404(MissionField, pk=field_id)
    message_text = request.POST.get("message", "").strip()

    _, created = MissionFieldRequest.objects.get_or_create(
        missionary=missionary,
        mission_field=field,
        defaults={"message": message_text},
    )

    if created:
        messages.success(
            request,
            f'Solicitação enviada para o campo "{field.name}". Aguarde aprovação.',
        )
    else:
        messages.info(request, "Você já solicitou este campo.")

    return redirect("missionary_dashboard")


@login_required
@require_POST
def cancel_field_request(request, request_id):
    missionary = getattr(request.user, "missionary_profile", None)
    if missionary is None:
        return redirect("missionary_dashboard")

    field_request = get_object_or_404(
        MissionFieldRequest,
        pk=request_id,
        missionary=missionary,
        status=MissionFieldRequest.Status.PENDING,
    )
    field_name = field_request.mission_field.name
    field_request.delete()
    messages.success(request, f'Solicitação para "{field_name}" cancelada.')
    return redirect("missionary_dashboard")


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


@login_required
def investor_dashboard(request):
    investor = getattr(request.user, "investor_profile", None)

    if investor is None:
        return render(
            request,
            "missions/investor_dashboard.html",
            {"investor": None},
        )

    adoptions = investor.adoptions.select_related(
        "missionary", "mission_field"
    ).order_by("-start_date")
    active_adoptions = [a for a in adoptions if a.status == Adoption.Status.ACTIVE]
    pending_adoptions = [a for a in adoptions if a.status == Adoption.Status.PENDING]
    closed_adoptions = [
        a
        for a in adoptions
        if a.status in (Adoption.Status.COMPLETED, Adoption.Status.CANCELLED)
    ]

    total_monthly = sum((a.monthly_value for a in active_adoptions), Decimal("0"))

    available_missionaries = (
        Missionary.objects.filter(is_public=True)
        .prefetch_related("mission_fields")
        .order_by("name")
    )

    return render(
        request,
        "missions/investor_dashboard.html",
        {
            "investor": investor,
            "active_adoptions": active_adoptions,
            "pending_adoptions": pending_adoptions,
            "closed_adoptions": closed_adoptions,
            "total_monthly": total_monthly,
            "available_missionaries": available_missionaries,
        },
    )


@login_required
@require_POST
def request_adoption(request):
    investor = getattr(request.user, "investor_profile", None)
    if investor is None:
        messages.error(request, "Seu perfil de investidor ainda não foi vinculado.")
        return redirect("investor_dashboard")

    missionary_id = request.POST.get("missionary_id")
    field_id = request.POST.get("mission_field_id")
    raw_value = request.POST.get("monthly_value", "").strip()

    missionary = get_object_or_404(Missionary, pk=missionary_id)
    field = get_object_or_404(MissionField, pk=field_id)

    if not missionary.mission_fields.filter(pk=field.pk).exists():
        messages.error(
            request, "Campo missionário não pertence ao missionário selecionado."
        )
        return redirect("investor_dashboard")

    try:
        monthly_value = Decimal(raw_value.replace(",", "."))
    except (InvalidOperation, AttributeError):
        messages.error(request, "Valor mensal inválido.")
        return redirect("investor_dashboard")

    if monthly_value <= 0:
        messages.error(request, "Valor mensal deve ser maior que zero.")
        return redirect("investor_dashboard")

    duplicate_exists = Adoption.objects.filter(
        investor=investor,
        missionary=missionary,
        mission_field=field,
        status__in=[Adoption.Status.PENDING, Adoption.Status.ACTIVE],
    ).exists()
    if duplicate_exists:
        messages.info(
            request,
            "Você já tem uma adoção ativa ou pendente para este missionário neste campo.",
        )
        return redirect("investor_dashboard")

    Adoption.objects.create(
        investor=investor,
        missionary=missionary,
        mission_field=field,
        monthly_value=monthly_value,
        start_date=timezone.now().date(),
        status=Adoption.Status.PENDING,
    )

    messages.success(
        request,
        f'Solicitação de adoção enviada para "{missionary.name}". Aguarde aprovação.',
    )
    return redirect("investor_dashboard")


@login_required
@require_POST
def cancel_adoption_request(request, adoption_id):
    investor = getattr(request.user, "investor_profile", None)
    if investor is None:
        return redirect("investor_dashboard")

    adoption = get_object_or_404(
        Adoption,
        pk=adoption_id,
        investor=investor,
        status=Adoption.Status.PENDING,
    )
    missionary_name = adoption.missionary.name
    adoption.delete()
    messages.success(
        request, f'Solicitação de adoção para "{missionary_name}" cancelada.'
    )
    return redirect("investor_dashboard")
