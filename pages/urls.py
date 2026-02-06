from django.urls import path

from . import views

urlpatterns = [
    path("perguntas-frequentes/", views.faq, name="faq"),
    path("contato/", views.contact, name="contact"),
    path("testemunhos/", views.testimonials, name="testimonials"),
    path("<slug:slug>/", views.page_detail, name="page_detail"),
]
