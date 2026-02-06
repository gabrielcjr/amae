from django.urls import path

from . import views

urlpatterns = [
    path('missionaries/', views.missionary_list, name='missionary_list'),
    path('missionaries/<int:pk>/', views.missionary_detail, name='missionary_detail'),
    path('churches/', views.church_list, name='church_list'),
    path('churches/<int:pk>/', views.church_detail, name='church_detail'),
]
