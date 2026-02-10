from django.urls import path

from . import views

urlpatterns = [
    path("campos-missionarios/", views.mission_field_map, name="mission_field_map"),
    path("missionaries/<int:pk>/", views.missionary_detail, name="missionary_detail"),
    path("investidores/<int:pk>/", views.investor_detail, name="investor_detail"),
]
