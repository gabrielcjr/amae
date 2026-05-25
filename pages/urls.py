from django.urls import path

from . import views

urlpatterns = [
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
    path("testimonials/", views.testimonials, name="testimonials"),
    path("<slug:slug>/", views.page_detail, name="page_detail"),
]
