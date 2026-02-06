import json

from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .models import Church, Missionary


def home(request):
    return render(request, 'home.html')


def missionary_list(request):
    missionaries = Missionary.objects.prefetch_related('mission_fields').all()
    return render(request, 'missions/missionary_list.html', {
        'missionaries': missionaries,
    })


def missionary_detail(request, pk):
    missionary = get_object_or_404(
        Missionary.objects.prefetch_related('mission_fields', 'adoptions__church'),
        pk=pk,
    )
    adoptions = missionary.adoptions.select_related('church').all()

    locations = []
    for field in missionary.mission_fields.prefetch_related('locations').all():
        for loc in field.locations.all():
            locations.append({
                'name': loc.name,
                'lat': float(loc.latitude),
                'lng': float(loc.longitude),
            })

    return render(request, 'missions/missionary_detail.html', {
        'missionary': missionary,
        'adoptions': adoptions,
        'locations': locations,
        'locations_json': json.dumps(locations),
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
    })


def church_list(request):
    churches = Church.objects.all()
    return render(request, 'missions/church_list.html', {
        'churches': churches,
    })


def church_detail(request, pk):
    church = get_object_or_404(Church, pk=pk)
    adoptions = church.adoptions.select_related('missionary').all()
    return render(request, 'missions/church_detail.html', {
        'church': church,
        'adoptions': adoptions,
    })
