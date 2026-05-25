from django.urls import path

from . import views

urlpatterns = [
    path("mission-fields/", views.mission_field_map, name="mission_field_map"),
    path("missionaries/", views.missionary_list, name="missionary_list"),
    path("missionaries/<int:pk>/", views.missionary_detail, name="missionary_detail"),
    path("investors/<int:pk>/", views.investor_detail, name="investor_detail"),
    path("dashboard/", views.dashboard_redirect, name="dashboard_redirect"),
    path(
        "dashboard/missionary/",
        views.missionary_dashboard,
        name="missionary_dashboard",
    ),
    path(
        "dashboard/missionary/request-field/<int:field_id>/",
        views.request_mission_field,
        name="request_mission_field",
    ),
    path(
        "dashboard/missionary/cancel-request/<int:request_id>/",
        views.cancel_field_request,
        name="cancel_field_request",
    ),
    path(
        "dashboard/investor/",
        views.investor_dashboard,
        name="investor_dashboard",
    ),
    path(
        "dashboard/investor/request-adoption/",
        views.request_adoption,
        name="request_adoption",
    ),
    path(
        "dashboard/investor/cancel-adoption/<int:adoption_id>/",
        views.cancel_adoption_request,
        name="cancel_adoption_request",
    ),
]
