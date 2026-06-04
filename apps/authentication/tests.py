"""
Unit tests for authentication endpoints.
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from apps.authentication.models import User
from apps.authentication.utils import generate_tokens, decode_token


class RegisterViewTests(TestCase):
    """Tests for POST /api/auth/register"""

    def setUp(self):
        self.client = Client()
        self.url = '/api/auth/register'

    def _post(self, data):
        return self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def test_register_success(self):
        """Valid registration returns 201 with tokens."""
        response = self._post({'name': 'Alice', 'email': 'alice@example.com', 'password': 'Str0ng!Pass'})
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertIn('tokens', body['data'])
        self.assertIn('access', body['data']['tokens'])
        self.assertIn('refresh', body['data']['tokens'])

    def test_register_duplicate_email(self):
        """Duplicate email returns 400."""
        User.objects.create_user(email='alice@example.com', name='Alice', password='pass')
        response = self._post({'name': 'Alice2', 'email': 'alice@example.com', 'password': 'Str0ng!Pass'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_register_invalid_email(self):
        """Invalid email returns 400."""
        response = self._post({'name': 'Alice', 'email': 'not-an-email', 'password': 'Str0ng!Pass'})
        self.assertEqual(response.status_code, 400)

    def test_register_missing_fields(self):
        """Missing required fields returns 400."""
        response = self._post({'email': 'alice@example.com'})
        self.assertEqual(response.status_code, 400)

    def test_register_short_password(self):
        """Password under 8 chars returns 400."""
        response = self._post({'name': 'Alice', 'email': 'alice@example.com', 'password': 'short'})
        self.assertEqual(response.status_code, 400)

    def test_trace_id_in_response(self):
        """Every response includes traceId."""
        response = self._post({'name': 'Bob', 'email': 'bob@example.com', 'password': 'Str0ng!Pass'})
        self.assertIn('traceId', response.json())


class LoginViewTests(TestCase):
    """Tests for POST /api/auth/login"""

    def setUp(self):
        self.client = Client()
        self.url = '/api/auth/login'
        self.user = User.objects.create_user(
            email='alice@example.com', name='Alice', password='Str0ng!Pass'
        )

    def _post(self, data):
        return self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def test_login_success(self):
        """Valid credentials return 200 with tokens."""
        response = self._post({'email': 'alice@example.com', 'password': 'Str0ng!Pass'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertIn('tokens', body['data'])

    def test_login_wrong_password(self):
        """Wrong password returns 401."""
        response = self._post({'email': 'alice@example.com', 'password': 'WrongPass!'})
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()['success'])

    def test_login_unknown_email(self):
        """Unknown email returns 401."""
        response = self._post({'email': 'nobody@example.com', 'password': 'Str0ng!Pass'})
        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        """Missing fields returns 400."""
        response = self._post({'email': 'alice@example.com'})
        self.assertEqual(response.status_code, 400)


class RefreshViewTests(TestCase):
    """Tests for POST /api/auth/refresh"""

    def setUp(self):
        self.client = Client()
        self.url = '/api/auth/refresh'
        self.user = User.objects.create_user(
            email='alice@example.com', name='Alice', password='pass1234'
        )

    def test_refresh_success(self):
        """Valid refresh token returns new token pair."""
        tokens = generate_tokens(self.user.id)
        response = self.client.post(
            self.url,
            data=json.dumps({'refresh': tokens['refresh']}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertIn('tokens', body['data'])

    def test_refresh_with_access_token_fails(self):
        """Using an access token as refresh token returns 401."""
        tokens = generate_tokens(self.user.id)
        response = self.client.post(
            self.url,
            data=json.dumps({'refresh': tokens['access']}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_refresh_invalid_token(self):
        """Garbage token returns 401."""
        response = self.client.post(
            self.url,
            data=json.dumps({'refresh': 'invalid.token.here'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)


class JWTUtilsTests(TestCase):
    """Unit tests for JWT token helpers."""

    def test_generate_and_decode_access(self):
        """Generated access token decodes correctly."""
        import uuid
        user_id = uuid.uuid4()
        tokens = generate_tokens(user_id)
        payload = decode_token(tokens['access'])
        self.assertEqual(payload['sub'], str(user_id))
        self.assertEqual(payload['type'], 'access')

    def test_generate_and_decode_refresh(self):
        """Generated refresh token decodes correctly."""
        import uuid
        user_id = uuid.uuid4()
        tokens = generate_tokens(user_id)
        payload = decode_token(tokens['refresh'])
        self.assertEqual(payload['sub'], str(user_id))
        self.assertEqual(payload['type'], 'refresh')

    def test_tampered_token_raises(self):
        """Tampered token raises InvalidTokenError."""
        import uuid
        import jwt
        tokens = generate_tokens(uuid.uuid4())
        with self.assertRaises(jwt.InvalidTokenError):
            decode_token(tokens['access'] + 'x')
