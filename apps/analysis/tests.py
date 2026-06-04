"""
Unit tests for AI analysis service (mocked Claude API).
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.utils import timezone

from apps.authentication.models import User
from apps.authentication.utils import generate_tokens
from apps.meetings.models import Meeting, TranscriptSegment
from apps.analysis.models import MeetingAnalysis, AnalysisItem, Citation
from apps.analysis.services.claude_service import (
    _parse_claude_response,
    _validate_citations,
)
from apps.analysis.services.prompt_builder import build_analysis_prompt


def _auth_headers(user_id):
    tokens = generate_tokens(user_id)
    return {'HTTP_AUTHORIZATION': f"Bearer {tokens['access']}"}


VALID_AI_RESPONSE = {
    'summary': [
        {
            'text': 'Team plans to launch next Friday.',
            'citations': [{'timestamp': '00:10', 'speaker': 'John', 'excerpt': 'We should launch next Friday.'}],
        }
    ],
    'actionItems': [
        {
            'task': 'Prepare release notes',
            'assignee': 'alice@example.com',
            'citations': [{'timestamp': '00:20', 'speaker': 'Alice', 'excerpt': 'I will prepare release notes.'}],
        }
    ],
    'decisions': [],
    'followUpSuggestions': [],
}


class ParseClaudeResponseTests(TestCase):
    """Unit tests for JSON parsing helper."""

    def test_valid_json_parsed(self):
        """Valid JSON string returns dict."""
        result = _parse_claude_response(json.dumps(VALID_AI_RESPONSE))
        self.assertIn('summary', result)

    def test_strips_markdown_fences(self):
        """JSON wrapped in ```json ... ``` is still parsed correctly."""
        wrapped = '```json\n' + json.dumps(VALID_AI_RESPONSE) + '\n```'
        result = _parse_claude_response(wrapped)
        self.assertIn('summary', result)

    def test_invalid_json_raises(self):
        """Non-JSON raises ValueError."""
        with self.assertRaises(ValueError):
            _parse_claude_response('This is not JSON.')


class ValidateCitationsTests(TestCase):
    """Unit tests for hallucination guard."""

    def test_item_with_citation_kept(self):
        """Items with citations are kept."""
        items = [{'text': 'decision', 'citations': [{'timestamp': '00:10'}]}]
        result = _validate_citations(items, 'decisions')
        self.assertEqual(len(result), 1)

    def test_item_without_citation_removed(self):
        """Items with no citations are dropped."""
        items = [{'text': 'invented decision', 'citations': []}]
        result = _validate_citations(items, 'decisions')
        self.assertEqual(len(result), 0)

    def test_mixed_items(self):
        """Only items with citations survive."""
        items = [
            {'text': 'grounded', 'citations': [{'timestamp': '00:05'}]},
            {'text': 'hallucinated', 'citations': []},
        ]
        result = _validate_citations(items, 'summary')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], 'grounded')


class PromptBuilderTests(TestCase):
    """Tests for prompt construction."""

    def setUp(self):
        self.user = User.objects.create_user(email='alice@example.com', name='Alice', password='pass1234')
        self.meeting = Meeting.objects.create(
            title='Sprint Planning',
            participants=['alice@example.com'],
            meeting_date=timezone.now(),
            created_by=self.user,
        )
        TranscriptSegment.objects.create(
            meeting=self.meeting, timestamp='00:10', speaker='John',
            text='We should launch next Friday.', order=0
        )
        TranscriptSegment.objects.create(
            meeting=self.meeting, timestamp='00:20', speaker='Alice',
            text='I will prepare release notes.', order=1
        )

    def test_prompt_contains_transcript(self):
        """Prompt includes all transcript lines."""
        prompt = build_analysis_prompt(self.meeting)
        self.assertIn('We should launch next Friday.', prompt)
        self.assertIn('I will prepare release notes.', prompt)
        self.assertIn('[00:10]', prompt)

    def test_prompt_has_grounding_instructions(self):
        """Prompt contains strict grounding instructions."""
        prompt = build_analysis_prompt(self.meeting)
        self.assertIn('Do NOT invent', prompt)
        self.assertIn('citation', prompt.lower())


class AnalyzeMeetingViewTests(TestCase):
    """Integration tests for POST /api/meetings/:id/analyze (mocked Claude)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='alice@example.com', name='Alice', password='pass1234')
        self.headers = _auth_headers(self.user.id)
        self.meeting = Meeting.objects.create(
            title='Sprint Planning',
            participants=['alice@example.com'],
            meeting_date=timezone.now(),
            created_by=self.user,
        )
        TranscriptSegment.objects.create(
            meeting=self.meeting, timestamp='00:10', speaker='John',
            text='We should launch next Friday.', order=0
        )
        TranscriptSegment.objects.create(
            meeting=self.meeting, timestamp='00:20', speaker='Alice',
            text='I will prepare release notes.', order=1
        )

    def _mock_claude_response(self, content: dict):
        """Build a mock OpenAI chat completion object."""
        mock_msg = MagicMock()
        mock_msg.choices = [MagicMock(message=MagicMock(content=json.dumps(content)))]
        return mock_msg


    @patch('apps.analysis.services.claude_service._client')
    def test_analyze_success(self, mock_client):
        """Successful analysis saves results and returns structured response."""
        mock_client.chat.completions.create.return_value = self._mock_claude_response(VALID_AI_RESPONSE)

        response = self.client.post(
            f'/api/meetings/{self.meeting.id}/analyze',
            content_type='application/json',
            **self.headers,
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['data']['status'], 'COMPLETED')
        self.assertEqual(len(body['data']['summary']), 1)
        self.assertEqual(len(body['data']['actionItems']), 1)

        # Verify citations were persisted
        analysis = MeetingAnalysis.objects.get(meeting=self.meeting)
        self.assertEqual(analysis.status, 'COMPLETED')
        items = AnalysisItem.objects.filter(analysis=analysis)
        self.assertTrue(items.exists())
        for item in items:
            self.assertTrue(item.citations.exists(), f"Item {item.id} has no citations")

    @patch('apps.analysis.services.claude_service._client')
    def test_analyze_drops_uncited_items(self, mock_client):
        """Items without citations are silently dropped."""
        response_with_uncited = {
            'summary': [
                {'text': 'Grounded summary.', 'citations': [{'timestamp': '00:10', 'speaker': 'John', 'excerpt': 'launch'}]},
                {'text': 'Hallucinated summary.', 'citations': []},
            ],
            'actionItems': [],
            'decisions': [],
            'followUpSuggestions': [],
        }
        mock_client.chat.completions.create.return_value = self._mock_claude_response(response_with_uncited)

        response = self.client.post(
            f'/api/meetings/{self.meeting.id}/analyze',
            content_type='application/json',
            **self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['data']['summary']), 1)

    def test_analyze_meeting_not_found(self):
        """Non-existent meeting returns 404."""
        import uuid
        response = self.client.post(
            f'/api/meetings/{uuid.uuid4()}/analyze',
            content_type='application/json',
            **self.headers,
        )
        self.assertEqual(response.status_code, 404)

    def test_analyze_unauthenticated(self):
        """Unauthenticated request returns 401."""
        response = self.client.post(
            f'/api/meetings/{self.meeting.id}/analyze',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
