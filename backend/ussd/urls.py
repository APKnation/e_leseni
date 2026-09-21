from django.urls import path

from . import views

urlpatterns = [
    path('gateway/', views.gateway, name='ussd-gateway'),
]
