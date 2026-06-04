"""
Builds the structured prompt sent to Claude for meeting analysis.
Strict grounding instructions prevent hallucination.
"""

import json
from apps.meetings.models import Meeting


def build_analysis_prompt(meeting: Meeting) -> str:
    """
    Construct the analysis prompt from a Meeting's transcript segments.

    The prompt instructs Claude to:
    - Only use information present in the transcript
    - Never invent attendees, decisions, or action items
    - Cite every insight back to transcript timestamps
    - Return only valid JSON with no surrounding text
    """
    segments = meeting.transcript_segments.all().order_by('order', 'id')

    transcript_lines = []
    for seg in segments:
        transcript_lines.append(f"[{seg.timestamp}] {seg.speaker}: {seg.text}")

    transcript_text = '\n'.join(transcript_lines)

    prompt = f"""You are a meeting analysis assistant. Your task is to analyze the following meeting transcript and extract insights.

STRICT RULES — you MUST follow these exactly:
1. Only use information that is EXPLICITLY stated in the transcript.
2. Do NOT invent attendees, decisions, action items, or outcomes.
3. Do NOT add information that is not present in the transcript.
4. Every item in summary, actionItems, decisions, and followUpSuggestions MUST include at least one citation.
5. Each citation must reference an actual timestamp from the transcript.
6. Copy each citation's "timestamp" EXACTLY as it appears in the transcript (e.g. if the transcript shows "00:10", use "00:10" — do NOT reformat it to "00:00:10" or any other format).
7. If there are no action items, decisions, or follow-ups in the transcript, return empty arrays.
8. Return ONLY valid JSON — no markdown, no code fences, no preamble, no explanation.

TRANSCRIPT:
{transcript_text}

Return a JSON object with this exact structure:
{{
  "summary": [
    {{
      "text": "<summary point derived only from transcript>",
      "citations": [
        {{"timestamp": "<timestamp from transcript>", "speaker": "<speaker name>", "excerpt": "<exact or near-exact quote>"}}
      ]
    }}
  ],
  "actionItems": [
    {{
      "task": "<task explicitly mentioned>",
      "assignee": "<person explicitly assigned, or null if not mentioned>",
      "citations": [
        {{"timestamp": "<timestamp>", "speaker": "<speaker>", "excerpt": "<quote>"}}
      ]
    }}
  ],
  "decisions": [
    {{
      "text": "<decision explicitly made in transcript>",
      "citations": [
        {{"timestamp": "<timestamp>", "speaker": "<speaker>", "excerpt": "<quote>"}}
      ]
    }}
  ],
  "followUpSuggestions": [
    {{
      "text": "<follow-up action grounded in transcript>",
      "citations": [
        {{"timestamp": "<timestamp>", "speaker": "<speaker>", "excerpt": "<quote>"}}
      ]
    }}
  ]
}}"""

    return prompt
