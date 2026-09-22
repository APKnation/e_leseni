from django.urls import path

from . import views

urlpatterns = [
    path('events/', views.EventStreamView.as_view(), name='events'),
]
