from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('auth/login/', TokenObtainPairView.as_view(serializer_class=views.LoginSerializer), name='auth-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='auth-verify'),
    path('auth/me/', views.MeView.as_view(), name='auth-me'),
    path('', include(router.urls)),
]
