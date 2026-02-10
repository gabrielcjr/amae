from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("cadastrar/investidor/", views.register_investor, name="register_investor"),
    path(
        "cadastrar/missionario/", views.register_missionary, name="register_missionary"
    ),
    path(
        "entrar/", LoginView.as_view(template_name="accounts/login.html"), name="login"
    ),
    path("sair/", LogoutView.as_view(), name="logout"),
]
