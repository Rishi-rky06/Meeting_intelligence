"""
Claude API service for meeting analysis.
Handles prompt execution, JSON parsing, citation validation, and DB persistence.
"""

import json
import logging
from datetime import datetime, timezone

from openai import OpenAI
from django.conf import settings
from django.db import transaction

from apps.analysis.models import MeetingAnalysis, AnalysisItem, Citation
from apps.analysis.services.prompt_builder import build_analysis_prompt
from apps.meetings.models import Meeting

logger = logging.getLogger(__name__)

_client = OpenAI(
    base_url=settings.GROQ_BASE_URL,
    api_key=settings.GROQ_API_KEY,
)



def _validate_citations(items: list, item_type: str) -> list:
    """
    Remove any items that have no citations (hallucination guard).
    Logs a warning for each dropped item.
    """
    valid = []
    for item in items:
        citations = item.get('citations', [])
        if not citations:
            logger.warning(
                f"Dropping {item_type} item with no citations — possible hallucination: "
                f"{str(item)[:120]}"
            )
            continue
        valid.append(item)
    return valid


def _parse_claude_response(raw_text: str) -> dict:
    """
    Parse the raw Claude response as JSON.
    Strips accidental markdown code fences if present.
    Raises ValueError on invalid JSON.
    """
    text = raw_text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1]) if lines[-1].strip() == '```' else '\n'.join(lines[1:])
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Claude returned non-JSON response: {exc}\nRaw: {raw_text[:500]}")


def _save_analysis_items(analysis: MeetingAnalysis, data: dict) -> list:
    """
    Persist AnalysisItem + Citation records from the parsed Claude response.
    Returns a list of dicts representing created action items for downstream use.
    """
    action_item_data = []

    type_map = {
        'summary': AnalysisItem.ItemType.SUMMARY,
        'actionItems': AnalysisItem.ItemType.ACTION_ITEM,
        'decisions': AnalysisItem.ItemType.DECISION,
        'followUpSuggestions': AnalysisItem.ItemType.FOLLOWUP,
    }

    for key, item_type in type_map.items():
        items = _validate_citations(data.get(key, []), key)
        for item in items:
            content = item.get('text') or item.get('task', '')
            assignee = item.get('assignee') or None

            analysis_item = AnalysisItem.objects.create(
                analysis=analysis,
                item_type=item_type,
                content=content,
                assignee=assignee,
            )

            for cit in item.get('citations', []):
                Citation.objects.create(
                    analysis_item=analysis_item,
                    timestamp=cit.get('timestamp', ''),
                    speaker=cit.get('speaker', ''),
                    text_excerpt=cit.get('excerpt', ''),
                )

            if item_type == AnalysisItem.ItemType.ACTION_ITEM:
                action_item_data.append({
                    'task': content,
                    'assignee': assignee,
                    'citations': item.get('citations', []),
                })

    return action_item_data


def analyze_meeting(meeting: Meeting) -> MeetingAnalysis:
    """
    Run Claude analysis on a meeting transcript and persist results.

    Steps:
    1. Create/reset MeetingAnalysis record (PENDING)
    2. Build prompt from transcript
    3. Call Claude API
    4. Parse + validate JSON response
    5. Save AnalysisItem + Citation records
    6. Auto-create ActionItem records from extracted action items
    7. Return completed MeetingAnalysis

    Raises Exception on Claude API or parsing failure (sets status to FAILED).
    """
    analysis, _ = MeetingAnalysis.objects.get_or_create(meeting=meeting)
    analysis.status = MeetingAnalysis.Status.PENDING
    analysis.raw_response = None
    analysis.error_message = None
    analysis.save()

    analysis.items.all().delete()

    prompt = build_analysis_prompt(meeting)

    logger.info(f"Calling Claude API for meeting id={meeting.id}")

    try:
        completion = _client.chat.completions.create(
            model=settings.GROQ_MODEL,
            max_tokens=4096,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                }
            ],
        )
        raw_text = completion.choices[0].message.content
    except Exception as exc:
        logger.error(f"Groq API error for meeting id={meeting.id}: {exc}")
        analysis.status = MeetingAnalysis.Status.FAILED
        analysis.error_message = str(exc)
        analysis.save()
        raise


    try:
        parsed = _parse_claude_response(raw_text)
    except ValueError as exc:
        logger.error(f"JSON parse error for meeting id={meeting.id}: {exc}")
        analysis.status = MeetingAnalysis.Status.FAILED
        analysis.error_message = str(exc)
        analysis.raw_response = {'raw': raw_text}
        analysis.save()
        raise

    with transaction.atomic():
        analysis.raw_response = parsed
        action_items_data = _save_analysis_items(analysis, parsed)
        analysis.status = MeetingAnalysis.Status.COMPLETED
        analysis.analyzed_at = datetime.now(tz=timezone.utc)
        analysis.save()

        _auto_create_action_items(meeting, action_items_data)

    logger.info(f"Analysis complete for meeting id={meeting.id}")
    return analysis


def _auto_create_action_items(meeting: Meeting, action_items_data: list):
    """
    Auto-create ActionItem records from AI-extracted action items.
    Skips items that have already been created for this meeting.
    """
    from apps.action_items.models import ActionItem

    existing = set(ActionItem.objects.filter(meeting=meeting).values_list('task', flat=True))

    for item in action_items_data:
        if item['task'] in existing:
            continue
        ActionItem.objects.create(
            meeting=meeting,
            task=item['task'],
            assignee=item['assignee'] or '',
            citations=[
                {
                    'timestamp': c.get('timestamp', ''),
                    'speaker': c.get('speaker', ''),
                    'excerpt': c.get('excerpt', ''),
                }
                for c in item.get('citations', [])
            ],
        )
