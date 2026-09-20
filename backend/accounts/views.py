from rest_framework import generics, permissions, viewsets

from .models import User
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Public endpoint to create an applicant account."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    """Return the logged-in user's profile."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff directory; search and filter by role/LGA."""

    queryset = User.objects.select_related('lga').all()
    serializer_class = UserSerializer
    filterset_fields = ['role', 'lga']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']
