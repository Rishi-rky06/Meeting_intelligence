# AI Approach

## Model

**Provider:** Groq (OpenAI-compatible API)  
**Model:** `llama-3.3-70b-versatile` (configurable via `GROQ_MODEL` env var)

The service talks to Groq through the official `openai` Python SDK, pointed at Groq's OpenAI-compatible base URL (`https://api.groq.com/openai/v1`). Because the integration speaks the OpenAI protocol, the provider/model can be swapped for Groq, OpenAI, OpenRouter, or any compatible endpoint by changing only the `GROQ_BASE_URL`, `GROQ_MODEL`, and `GROQ_API_KEY` environment variables, with no code changes.

---

## Prompt Design

The prompt is constructed in `apps/analysis/services/prompt_builder.py`. It follows these principles:

### 1. Role priming
The prompt opens with a clear role definition:
```
You are a meeting analysis assistant. Your task is to analyze the following meeting transcript and extract insights.
```

### 2. Explicit grounding constraints (hallucination prevention)
A numbered rule block appears before the transcript:
```
STRICT RULES — you MUST follow these exactly:
1. Only use information that is EXPLICITLY stated in the transcript.
2. Do NOT invent attendees, decisions, action items, or outcomes.
3. Do NOT add information that is not present in the transcript.
4. Every item ... MUST include at least one citation.
5. Each citation must reference an actual timestamp from the transcript.
6. If there are no action items, decisions, or follow-ups, return empty arrays.
7. Return ONLY valid JSON — no markdown, no code fences, no preamble.
```

### 3. Structured transcript injection
Each transcript segment is formatted as `[timestamp] speaker: text`, giving the model clear timestamp anchors to cite.

### 4. Strict output schema
The prompt specifies the exact JSON structure expected, including the citation shape. This eliminates ambiguity about the output format.

---

## Citation Strategy

Every generated insight is required to cite ≥ 1 transcript segment. The citation includes:
- `timestamp` — the segment's timestamp (e.g., `"00:10"`)
- `speaker` — who said it
- `excerpt` — the verbatim or near-verbatim quote

Citations are stored in the `Citation` model and returned in every API response alongside the insight they support.

---

## Hallucination Prevention

Three-layer defence:

1. **Prompt-level:** Numbered rules explicitly forbid invented content. Empty arrays are permitted (and encouraged) when no relevant content exists in the transcript.

2. **Post-processing validation (`_validate_citations`):** After parsing the model response, every item is checked for at least one citation. Items with no citations are silently dropped and logged as warnings (`"Dropping X item with no citations — possible hallucination"`). This means a hallucinated item that slips through the prompt rules will be caught and discarded before DB persistence.

3. **JSON parsing safety:** The `_parse_claude_response` function strips markdown code fences if present, then parses strict JSON. Any response that is not valid JSON sets the analysis status to `FAILED` rather than storing corrupt data.

---

## Output Validation Strategy

After receiving the model response:
1. Strip accidental markdown fences
2. Parse as strict JSON (fail fast on invalid JSON)
3. Validate each section (`summary`, `actionItems`, `decisions`, `followUpSuggestions`)
4. Drop any item with empty or missing `citations`
5. Persist only validated items atomically in a single DB transaction

---

## Auto-created Action Items

When analysis completes, action items extracted by the model are automatically promoted to `ActionItem` records in the database. This allows the reminder scheduler to detect overdue items without requiring manual data entry after every analysis.

---

## Known Limitations

1. **Long transcripts:** Very long transcripts may approach context window limits or produce degraded output. A chunking/summarization pipeline would be needed for hour-long calls.

2. **Citation accuracy:** The model cites timestamps from the formatted transcript. If the transcript has duplicate timestamps (rare but possible), citations may be ambiguous.

3. **No re-ranking or confidence scoring:** All generated items are treated equally. A production system might add confidence filtering.

4. **Email addresses in assignees:** The model extracts assignee names (e.g., "Alice") not email addresses. The `assignee` field on `ActionItem` may contain a name rather than an email. This is noted as a limitation — a name-to-email lookup would require additional context not in the transcript.

5. **Single-shot prompting:** The current approach uses one prompt → one response. A multi-turn conversation or chain-of-thought approach could improve extraction quality for complex transcripts.

6. **Free-tier rate limits:** The model runs on Groq's free tier, which has per-minute and daily request limits. Under heavy use the API may return a `429`, which surfaces as a graceful `ANALYSIS_FAILED` response rather than a crash. The `_parse_claude_response` parser strips code fences and fails gracefully (status `FAILED`) when JSON is invalid, and the citation-validation step drops any uncited items. Because the provider is abstracted behind the `openai` SDK + `GROQ_BASE_URL`/`GROQ_MODEL` env vars, switching providers or upgrading is a one-line config change.
