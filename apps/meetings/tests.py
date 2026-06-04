"""
Unit tests for meeting CRUD endpoints.
"""

import json
from django.test import TestCase, Client
from apps.authentication.models import User
from apps.authentication.utils import generate_tokens
from apps.meetings.models import Meeting, TranscriptSegment

SAMPLE_TRANSCRIPT = [
    {'timestamp': '00:10', 'speaker': 'John', 'text': 'We should launch next Friday.'},
    {'timestamp': '00:20', 'speaker': 'Alice', 'text': 'I will prepare release notes.'},
]


def _auth_headers(user_id):
    """Return Authorization header dict for a given user."""
    tokens = generate_tokens(user_id)
    return {'HTTP_AUTHORIZATION': f"Bearer {tokens['access']}"}


class CreateMeetingTests(TestCase):
    """Tests for POST /api/meetings"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='alice@example.com', name='Alice', password='pass1234'
        )
        self.headers = _auth_headers(self.user.id)

    def _post(self, data):
        return self.client.post(
            '/api/meetings/',
            data=json.dumps(data),
            content_type='application/json',
            **self.headers,
        )

    def test_create_meeting_success(self):
        """Valid payload creates meeting and transcript segments."""
        response = self._post({
            'title': 'Sprint Planning',
            'participants': ['alice@example.com', 'bob@example.com'],
            'meetingDate': '2026-05-20T10:00:00Z',
            'transcript': SAMPLE_TRANSCRIPT,
        })
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['data']['title'], 'Sprint Planning')
        self.assertEqual(len(body['data']['transcript']), 2)

    def test_create_meeting_missing_title(self):
        """Missing title returns 400."""
        response = self._post({
            'participants': ['alice@example.com'],
            'meetingDate': '2026-05-20T10:00:00Z',
            'transcript': SAMPLE_TRANSCRIPT,
        })
        self.assertEqual(response.status_code, 400)

    def test_create_meeting_invalid_email_participant(self):
        """Invalid participant email returns 400."""
        response = self._post({
            'title': 'Test',
            'participants': ['not-an-email'],
            'meetingDate': '2026-05-20T10:00:00Z',
            'transcript': SAMPLE_TRANSCRIPT,
        })
        self.assertEqual(response.status_code, 400)

    def test_create_meeting_empty_transcript(self):
        """Empty transcript returns 400."""
        response = self._post({
            'title': 'Test',
            'participants': ['alice@example.com'],
            'meetingDate': '2026-05-20T10:00:00Z',
            'transcript': [],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_meeting_unauthenticated(self):
        """Unauthenticated request returns 401."""
        response = self.client.post(
            '/api/meetings/',
            data=json.dumps({'title': 'Test'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)


class GetMeetingTests(TestCase):
    """Tests for GET /api/meetings/:id"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='alice@example.com', name='Alice', password='pass1234'
        )
        self.headers = _auth_headers(self.user.id)
        self.meeting = Meeting.objects.create(
            title='Sprint Planning',
            participants=['alice@example.com'],
            meeting_date='2026-05-20T10:00:00Z',
            created_by=self.user,
        )
        TranscriptSegment.objects.create(
            meeting=self.meeting, timestamp='00:10', speaker='John',
            text='We should launch.', order=0
        )

    def test_get_meeting_success(self):
        """Owner can retrieve their meeting."""
        response = self.client.get(
            f'/api/meetings/{self.meeting.id}',
            **self.headers,
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['data']['id'], str(self.meeting.id))
        self.assertEqual(len(body['data']['transcript']), 1)

    def test_get_meeting_not_found(self):
        """Non-existent meeting returns 404."""
        import uuid
        response = self.client.get(
            f'/api/meetings/{uuid.uuid4()}',
            **self.headers,
        )
        self.assertEqual(response.status_code, 404)

    def test_get_meeting_other_user(self):
        """Another user cannot access the meeting."""
        other = User.objects.create_user(email='bob@example.com', name='Bob', password='pass1234')
        other_headers = _auth_headers(other.id)
        response = self.client.get(
            f'/api/meetings/{self.meeting.id}',
            **other_headers,
        )
        self.assertEqual(response.status_code, 404)


class ListMeetingsTests(TestCase):
    """Tests for GET /api/meetings (paginated list)"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='alice@example.com', name='Alice', password='pass1234'
        )
        self.headers = _auth_headers(self.user.id)
        for i in range(3):
            Meeting.objects.create(
                title=f'Meeting {i}',
                participants=['alice@example.com'],
                meeting_date='2026-05-20T10:00:00Z',
                created_by=self.user,
            )

    def test_list_meetings_returns_only_own(self):
        """List only returns meetings owned by the authenticated user."""
        other = User.objects.create_user(email='bob@example.com', name='Bob', password='pass1234')
        Meeting.objects.create(
            title='Bob meeting', participants=['bob@example.com'],
            meeting_date='2026-05-20T10:00:00Z', created_by=other,
        )
        response = self.client.get('/api/meetings/', **self.headers)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['data']['pagination']['count'], 3)

    def test_list_meetings_pagination(self):
        """Pagination metadata is present."""
        response = self.client.get('/api/meetings/?page=1&pageSize=2', **self.headers)
        self.assertEqual(response.status_code, 200)
        pagination = response.json()['data']['pagination']
        self.assertIn('totalPages', pagination)
        self.assertEqual(pagination['pageSize'], 2)
