"""
Unit tests for action item management and overdue detection.
"""

import json
import uuid
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from apps.authentication.models import User
from apps.authentication.utils import generate_tokens
from apps.meetings.models import Meeting
from apps.action_items.models import ActionItem


def _auth_headers(user_id):
    tokens = generate_tokens(user_id)
    return {'HTTP_AUTHORIZATION': f"Bearer {tokens['access']}"}


def _make_meeting(user):
    return Meeting.objects.create(
        title='Test Meeting',
        participants=[user.email],
        meeting_date=timezone.now(),
        created_by=user,
    )


class CreateActionItemTests(TestCase):
    """Tests for POST /api/action-items"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='alice@example.com', name='Alice', password='pass1234')
        self.headers = _auth_headers(self.user.id)
        self.meeting = _make_meeting(self.user)

    def _post(self, data):
        return self.client.post(
            '/api/action-items/',
            data=json.dumps(data),
            content_type='application/json',
            **self.headers,
        )

    def test_create_action_item_success(self):
        """Valid payload creates action item."""
        response = self._post({
            'task': 'Prepare release notes',
            'assignee': 'alice@example.com',
            'meetingId': str(self.meeting.id),
            'dueDate': '2026-06-01T10:00:00Z',
        })
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['data']['task'], 'Prepare release notes')
        self.assertEqual(body['data']['status'], 'PENDING')

    def test_create_action_item_without_meeting(self):
        """Action item can be created without a meetingId."""
        response = self._post({'task': 'Follow up with team'})
        self.assertEqual(response.status_code, 201)

    def test_create_action_item_invalid_assignee(self):
        """Invalid assignee email returns 400."""
        response = self._post({'task': 'Do something', 'assignee': 'not-an-email'})
        self.assertEqual(response.status_code, 400)

    def test_create_action_item_missing_task(self):
        """Missing task returns 400."""
        response = self._post({'assignee': 'alice@example.com'})
        self.assertEqual(response.status_code, 400)

    def test_create_action_item_unauthenticated(self):
        """Unauthenticated returns 401."""
        response = self.client.post(
            '/api/action-items/',
            data=json.dumps({'task': 'Test'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)


class UpdateStatusTests(TestCase):
    """Tests for PATCH /api/action-items/:id/status"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='alice@example.com', name='Alice', password='pass1234')
        self.headers = _auth_headers(self.user.id)
        self.meeting = _make_meeting(self.user)
        self.item = ActionItem.objects.create(
            meeting=self.meeting,
            task='Prepare release notes',
            assignee='alice@example.com',
        )

    def _patch(self, item_id, data):
        return self.client.patch(
            f'/api/action-items/{item_id}/status',
            data=json.dumps(data),
            content_type='application/json',
            **self.headers,
        )

    def test_update_status_to_in_progress(self):
        """Status can be updated to IN_PROGRESS."""
        response = self._patch(self.item.id, {'status': 'IN_PROGRESS'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['status'], 'IN_PROGRESS')

    def test_update_status_to_completed(self):
        """Status can be updated to COMPLETED."""
        response = self._patch(self.item.id, {'status': 'COMPLETED'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['status'], 'COMPLETED')

    def test_update_status_invalid_value(self):
        """Invalid status value returns 400."""
        response = self._patch(self.item.id, {'status': 'DONE'})
        self.assertEqual(response.status_code, 400)

    def test_update_status_not_found(self):
        """Non-existent item returns 404."""
        response = self._patch(uuid.uuid4(), {'status': 'COMPLETED'})
        self.assertEqual(response.status_code, 404)


class ListActionItemsTests(TestCase):
    """Tests for GET /api/action-items with filters."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='alice@example.com', name='Alice', password='pass1234')
        self.headers = _auth_headers(self.user.id)
        self.meeting = _make_meeting(self.user)

        ActionItem.objects.create(
            meeting=self.meeting, task='Task A', assignee='alice@example.com', status='PENDING'
        )
        ActionItem.objects.create(
            meeting=self.meeting, task='Task B', assignee='bob@example.com', status='COMPLETED'
        )
        ActionItem.objects.create(
            meeting=self.meeting, task='Task C', assignee='alice@example.com', status='IN_PROGRESS'
        )

    def test_list_all(self):
        """List returns all items for user's meetings."""
        response = self.client.get('/api/action-items/', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['pagination']['count'], 3)

    def test_filter_by_status(self):
        """Filter by status works correctly."""
        response = self.client.get('/api/action-items/?status=PENDING', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['pagination']['count'], 1)

    def test_filter_by_assignee(self):
        """Filter by assignee works correctly."""
        response = self.client.get('/api/action-items/?assignee=alice@example.com', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['pagination']['count'], 2)

    def test_filter_by_meeting_id(self):
        """Filter by meetingId works correctly."""
        response = self.client.get(
            f'/api/action-items/?meetingId={self.meeting.id}', **self.headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['pagination']['count'], 3)

    def test_filter_invalid_status(self):
        """Invalid status filter returns 400."""
        response = self.client.get('/api/action-items/?status=INVALID', **self.headers)
        self.assertEqual(response.status_code, 400)


class OverdueActionItemTests(TestCase):
    """Tests for GET /api/action-items/overdue and overdue detection logic."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='alice@example.com', name='Alice', password='pass1234')
        self.headers = _auth_headers(self.user.id)
        self.meeting = _make_meeting(self.user)

    def test_overdue_items_returned(self):
        """Items with past due_date and non-COMPLETED status are overdue."""
        past = timezone.now() - timedelta(days=2)
        ActionItem.objects.create(
            meeting=self.meeting, task='Overdue task', due_date=past, status='PENDING'
        )
        response = self.client.get('/api/action-items/overdue', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['pagination']['count'], 1)

    def test_completed_items_not_overdue(self):
        """COMPLETED items are not returned even if past due."""
        past = timezone.now() - timedelta(days=2)
        ActionItem.objects.create(
            meeting=self.meeting, task='Done task', due_date=past, status='COMPLETED'
        )
        response = self.client.get('/api/action-items/overdue', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['pagination']['count'], 0)

    def test_future_due_date_not_overdue(self):
        """Items with future due_date are not overdue."""
        future = timezone.now() + timedelta(days=2)
        ActionItem.objects.create(
            meeting=self.meeting, task='Future task', due_date=future, status='PENDING'
        )
        response = self.client.get('/api/action-items/overdue', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['pagination']['count'], 0)

    def test_is_overdue_property(self):
        """ActionItem.is_overdue property works correctly."""
        past = timezone.now() - timedelta(days=1)
        item = ActionItem(task='test', due_date=past, status='PENDING')
        self.assertTrue(item.is_overdue)

        item.status = 'COMPLETED'
        self.assertFalse(item.is_overdue)

        item.status = 'PENDING'
        item.due_date = timezone.now() + timedelta(days=1)
        self.assertFalse(item.is_overdue)
