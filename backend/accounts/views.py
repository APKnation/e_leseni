from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import PasswordResetToken, User
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)


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


class PasswordResetRequestView(generics.GenericAPIView):
    """Step 1: verify username + phone, return a reset token.

    In production replace the token response with an SMS dispatch.
    For the demo the token is returned directly so the frontend can pass it
    to step 2 without any SMS infrastructure.
    """

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        reset_token = PasswordResetToken.generate_for(user)
        return Response({
            'detail': 'Account verified. Use the token below to reset your password.',
            'token': reset_token.token,          # In production: send via SMS, hide from response
            'expires_in_minutes': PasswordResetToken.TOKEN_EXPIRY_MINUTES,
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    """Step 2: consume token and set a new password."""

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Password updated successfully. You can now log in.'},
            status=status.HTTP_200_OK,
        )
