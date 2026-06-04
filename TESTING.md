# Testing

## Running Tests

```bash
DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py test apps.authentication apps.meetings apps.action_items apps.analysis --verbosity=2
```

**Result: 56 tests, 0 failures**

Tests use an in-memory SQLite database and mock the Groq/LLM API — no external services required.

---

## Test Coverage by Module

### Authentication (16 tests)

| Test | Scenario |
|------|----------|
| `test_register_success` | Valid registration → 201, tokens in response |
| `test_register_duplicate_email` | Duplicate email → 400 |
| `test_register_invalid_email` | Bad email format → 400 |
| `test_register_missing_fields` | Missing name/email/password → 400 |
| `test_register_short_password` | Password < 8 chars → 400 |
| `test_trace_id_in_response` | Every response includes traceId |
| `test_login_success` | Valid credentials → 200, tokens |
| `test_login_wrong_password` | Wrong password → 401 |
| `test_login_unknown_email` | Unknown email → 401 |
| `test_login_missing_fields` | Missing fields → 400 |
| `test_refresh_success` | Valid refresh token → new token pair |
| `test_refresh_with_access_token_fails` | Access token used as refresh → 401 |
| `test_refresh_invalid_token` | Garbage token → 401 |
| `test_generate_and_decode_access` | Access token round-trips correctly |
| `test_generate_and_decode_refresh` | Refresh token round-trips correctly |
| `test_tampered_token_raises` | Modified token raises InvalidTokenError |

### Meetings (10 tests)

| Test | Scenario |
|------|----------|
| `test_create_meeting_success` | Valid payload → 201, transcript segments saved |
| `test_create_meeting_missing_title` | Missing title → 400 |
| `test_create_meeting_invalid_email_participant` | Bad participant email → 400 |
| `test_create_meeting_empty_transcript` | Empty transcript → 400 |
| `test_create_meeting_unauthenticated` | No token → 401 |
| `test_get_meeting_success` | Owner can retrieve meeting + transcript |
| `test_get_meeting_not_found` | Non-existent ID → 404 |
| `test_get_meeting_other_user` | Other user's meeting → 404 |
| `test_list_meetings_returns_only_own` | Only authenticated user's meetings returned |
| `test_list_meetings_pagination` | Pagination metadata present |

### Action Items (17 tests)

| Test | Scenario |
|------|----------|
| `test_create_action_item_success` | Valid payload → 201, default PENDING status |
| `test_create_action_item_without_meeting` | No meetingId → allowed |
| `test_create_action_item_invalid_assignee` | Bad assignee email → 400 |
| `test_create_action_item_missing_task` | Missing task → 400 |
| `test_create_action_item_unauthenticated` | No token → 401 |
| `test_update_status_to_in_progress` | Status → IN_PROGRESS works |
| `test_update_status_to_completed` | Status → COMPLETED works |
| `test_update_status_invalid_value` | Invalid status → 400 |
| `test_update_status_not_found` | Non-existent item → 404 |
| `test_list_all` | Lists all items for user's meetings |
| `test_filter_by_status` | ?status=PENDING filters correctly |
| `test_filter_by_assignee` | ?assignee= filters correctly |
| `test_filter_by_meeting_id` | ?meetingId= filters correctly |
| `test_filter_invalid_status` | Invalid ?status= → 400 |
| `test_overdue_items_returned` | Past due, non-COMPLETED items appear in /overdue |
| `test_completed_items_not_overdue` | COMPLETED items excluded from /overdue |
| `test_future_due_date_not_overdue` | Future due_date excluded from /overdue |
| `test_is_overdue_property` | `is_overdue` model property works correctly |

### AI Analysis (13 tests)

| Test | Scenario |
|------|----------|
| `test_valid_json_parsed` | Valid JSON response → dict |
| `test_strips_markdown_fences` | Code-fenced JSON → parsed correctly |
| `test_invalid_json_raises` | Non-JSON → ValueError |
| `test_item_with_citation_kept` | Item with citation → kept |
| `test_item_without_citation_removed` | Item without citation → dropped |
| `test_mixed_items` | Mixed cited/uncited → only cited survive |
| `test_prompt_contains_transcript` | Prompt includes all transcript segments |
| `test_prompt_has_grounding_instructions` | Prompt includes hallucination prevention rules |
| `test_analyze_success` | Valid LLM response → 200, DB records created, all items have citations |
| `test_analyze_drops_uncited_items` | Uncited items in response → dropped from DB |
| `test_analyze_meeting_not_found` | Non-existent meeting → 404 |
| `test_analyze_unauthenticated` | No token → 401 |

---

## Edge Cases Considered

- **Duplicate email registration** — rejected with clear error
- **Wrong token type** — using refresh token as access token is rejected
- **Tampered JWT** — signature validation catches modifications
- **Hallucinated analysis items** — citation validation drops uncited items
- **Re-analysis** — calling `/analyze` again replaces previous results atomically
- **User isolation** — users can only see their own meetings and action items
- **Empty overdue list** — returns empty paginated result, not an error
- **Action item without meeting** — allowed (manual creation)
- **Invalid status filter** — returns 400 with clear error message

---

## Limitations Discovered

1. **No test for scheduler job** — `send_overdue_reminders()` is not unit tested due to Resend API dependency. The Resend call would need to be mocked.

2. **No test for email service** — `send_reminder_email()` is not covered. Integration tests would require a Resend sandbox.

3. **Groq API key not tested end-to-end** — All AI tests mock the `_client`. A true end-to-end test would require a live API key and would consume Groq's free-tier quota in CI.

4. **No load/performance tests** — Not in scope for this assignment.
