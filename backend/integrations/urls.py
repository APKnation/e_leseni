from django.urls import path

from . import views

urlpatterns = [
    path('mock/brela/verify/', views.mock_brela_verify, name='mock-brela-verify'),
    path('mock/tra/verify-tin/', views.mock_tra_verify_tin, name='mock-tra-verify-tin'),
    path('mock/gepg/bill/', views.mock_gepg_bill, name='mock-gepg-bill'),
    path('mock/gepg/reconcile/', views.mock_gepg_reconcile, name='mock-gepg-reconcile'),
]
