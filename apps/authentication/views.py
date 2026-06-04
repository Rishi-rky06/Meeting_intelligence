"""
Authentication views: register, login, refresh, logout.
"""

import logging
import jwt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.authentication.models import User
from apps.authentication.serializers import RegisterSerializer, LoginSerializer, RefreshSerializer, UserSerializer
from apps.authentication.utils import generate_tokens, decode_token
from core.response import success_response, error_response

logger = logging.getLogger(__name__)


@extend_schema(
    request=RegisterSerializer,
    responses={201: OpenApiResponse(description='User created; returns user data and JWT token pair.')},
    tags=['auth'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user.
    Returns user data and a JWT token pair on success.
    """
    serializer = RegisterSerializer(data=request.data)
    if not serializer.is_valid():
        from rest_framework.exceptions import ValidationError
        raise ValidationError(serializer.errors)

    user = serializer.save()
    tokens = generate_tokens(user.id)

    logger.info(f"New user registered: {user.email}")

    return success_response(
        {
            'user': UserSerializer(user).data,
            'tokens': tokens,
        },
        request=request,
        status=201,
    )


@extend_schema(
    request=LoginSerializer,
    responses={200: OpenApiResponse(description='Returns user data and JWT token pair.')},
    tags=['auth'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Authenticate a user with email and password.
    Returns a JWT token pair on success.
    """
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        from rest_framework.exceptions import ValidationError
        raise ValidationError(serializer.errors)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return error_response('INVALID_CREDENTIALS', 'Invalid email or password.', request, status=401)

    if not user.is_active:
        return error_response('ACCOUNT_DISABLED', 'This account has been disabled.', request, status=401)

    if not user.check_password(password):
        return error_response('INVALID_CREDENTIALS', 'Invalid email or password.', request, status=401)

    tokens = generate_tokens(user.id)
    logger.info(f"User logged in: {user.email}")

    return success_response(
        {
            'user': UserSerializer(user).data,
            'tokens': tokens,
        },
        request=request,
    )


@extend_schema(
    request=RefreshSerializer,
    responses={200: OpenApiResponse(description='Returns a new JWT token pair.')},
    tags=['auth'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh(request):
    """
    Exchange a valid refresh token for a new access/refresh token pair.
    """
    serializer = RefreshSerializer(data=request.data)
    if not serializer.is_valid():
        from rest_framework.exceptions import ValidationError
        raise ValidationError(serializer.errors)

    token = serializer.validated_data['refresh']

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        return error_response('TOKEN_EXPIRED', 'Refresh token has expired.', request, status=401)
    except jwt.InvalidTokenError as exc:
        return error_response('INVALID_TOKEN', f'Invalid token: {exc}', request, status=401)

    if payload.get('type') != 'refresh':
        return error_response('INVALID_TOKEN', 'Token type must be refresh.', request, status=401)

    try:
        user = User.objects.get(id=payload['sub'])
    except User.DoesNotExist:
        return error_response('INVALID_TOKEN', 'User not found.', request, status=401)

    if not user.is_active:
        return error_response('ACCOUNT_DISABLED', 'This account has been disabled.', request, status=401)

    tokens = generate_tokens(user.id)
    logger.info(f"Tokens refreshed for user: {user.email}")

    return success_response({'tokens': tokens}, request=request)


@extend_schema(
    request=None,
    responses={200: OpenApiResponse(description='Logged out; client should discard tokens.')},
    tags=['auth'],
)
@api_view(['POST'])
def logout(request):
    """
    Logout endpoint — client must discard tokens.
    Stateless JWT means we cannot invalidate server-side without a denylist.
    Returns 200 so the client knows to clear stored tokens.
    """
    logger.info(f"User logged out: user_id={request.user_id}")
    return success_response({'message': 'Logged out successfully.'}, request=request)
