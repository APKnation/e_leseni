from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import User
from .serializers import LoginSerializer, ProfileUpdateSerializer, RegisterSerializer, UserSerializer


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


class MeUpdateView(generics.UpdateAPIView):
    """PATCH the logged-in user's profile (e.g. add a NIDA number later)."""

    serializer_class = ProfileUpdateSerializer

    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mock_nida_verify(request):
    """DEMO NIDA verification: any 20-digit number is valid.

    Returns the citizen name the real NIDA API would provide so the UI can
    show what NIDA returned. Swap the rule for the real REST integration.
    """
    nida = (request.data.get('nida_number') or '').strip()
    first = (request.data.get('first_name') or '').strip()
    last = (request.data.get('last_name') or '').strip()
    valid = nida.isdigit() and len(nida) == 20
    return Response({
        'valid': valid,
        'nida_number': nida if valid else '',
        # The real API returns the registered name; the demo echoes the input.
        'full_name': f'{first} {last}'.strip() if valid else '',
        'source': 'NIDA (demo)',
    })


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Staff directory; search and filter by role/LGA."""

    queryset = User.objects.select_related('lga').all()
    serializer_class = UserSerializer
    filterset_fields = ['role', 'lga']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']
