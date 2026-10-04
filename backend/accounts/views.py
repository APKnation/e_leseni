from django.db import models
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import PasswordResetToken, User
from .serializers import (
    AdminPasswordResetSerializer,
    ChangePasswordSerializer,
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(UserSerializer(instance, context={'request': request}).data)


class ChangePasswordView(generics.GenericAPIView):
    """POST to change the currently logged-in user's password.

    Body: { "current_password": "...", "new_password": "..." }
    Returns 200 on success; the client must log in again to get fresh tokens.
    """

    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Password changed successfully. Please log in again.'},
            status=status.HTTP_200_OK,
        )


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


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allows staff/authenticated users to view the directory, but only ADMIN or superuser can create/modify users."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role == User.Roles.ADMIN or request.user.is_superuser


class UserViewSet(viewsets.ModelViewSet):
    """User directory and full CRUD management for administrators."""

    queryset = User.objects.select_related('lga').all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['role', 'lga', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        user = self.get_object()
        serializer = AdminPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'detail': f'Password updated successfully for {user.username}.'})

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response({'detail': 'You cannot deactivate your own account.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        return Response({
            'detail': f'User {user.username} is now {"active" if user.is_active else "inactive"}.',
            'is_active': user.is_active,
        })

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            return Response({'detail': 'You cannot delete your own account.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return super().destroy(request, *args, **kwargs)
        except models.ProtectedError:
            user.is_active = False
            user.save(update_fields=['is_active'])
            return Response(
                {
                    'detail': f'User {user.username} has linked records (applications, inspections, or audits) and was deactivated instead of deleted.',
                    'deactivated': True,
                },
                status=status.HTTP_200_OK,
            )


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
