# Changelog

## [1.0.0] — 2026-06-03

### Phase 1: Project Setup
- Created Django project with split settings (`base`, `development`, `production`, `testing`)
- Added `requirements.txt` with all dependencies
- Configured `python-decouple` for all environment variables
- Set up `config/urls.py` with API routing and Swagger endpoints
- Added `.env.example` template and `.gitignore`

### Phase 2: Authentication
- Implemented custom `User` model (UUID PK, email-based login)
- Built JWT token generation and decoding utilities using PyJWT only
- Created `JWTAuthMiddleware` — decodes Bearer tokens and attaches `request.user_id`
- Implemented `IsAuthenticatedViaJWT` DRF permission class
- Built register, login, refresh, and logout endpoints
- Passwords hashed via Django's PBKDF2 hasher

### Phase 3: Core Infrastructure
- `TraceIDMiddleware` — reads `X-Trace-ID` header or generates UUID4, attaches to request and response
- `StructuredFormatter` — thread-local logging with `timestamp | trace_id | level | method | path | status | message`
- `success_response()` / `error_response()` — unified API envelope helpers
- Global exception handler — all exceptions converted to unified format, 500 for unhandled errors
- `StandardPagination` — page-based pagination wrapped in unified envelope
- `validate_email_address()` / `validate_email_list()` — reusable validators

### Phase 4: Meeting Management
- `Meeting` model (UUID PK, title, participants JSONField, meeting_date, FK to User)
- `TranscriptSegment` model (timestamp, speaker, text, order)
- Create meeting with bulk transcript segment creation
- Get single meeting (owner-scoped)
- List meetings with pagination (owner-scoped)
- Input validation: participants must be valid email list, transcript non-empty

### Phase 5: AI Analysis
- `MeetingAnalysis` model (OneToOne with Meeting, status, raw_response)
- `AnalysisItem` model (type: SUMMARY/ACTION_ITEM/DECISION/FOLLOWUP, content, assignee)
- `Citation` model (FK to AnalysisItem, timestamp, speaker, text_excerpt)
- `build_analysis_prompt()` — grounded prompt with strict hallucination prevention rules
- `analyze_meeting()` — Groq (Llama 3.3 70B) API call, JSON parsing, citation validation, atomic DB persistence
- `_validate_citations()` — drops items without citations (hallucination guard)
- Auto-creates `ActionItem` records from AI-extracted action items
- Serializers for structured response with summary/actionItems/decisions/followUpSuggestions

### Phase 6: Action Item Management
- `ActionItem` model (UUID PK, meeting FK, task, assignee, due_date, status, citations JSONField)
- `ReminderLog` model (FK to ActionItem, channel, status, error_message)
- Create action item (with or without meeting association)
- Update status (PENDING → IN_PROGRESS → COMPLETED)
- List action items with filters: status, assignee, meetingId
- `GET /api/action-items/overdue` — items where status != COMPLETED and due_date < now
- `is_overdue` property on ActionItem model

### Phase 7: Scheduler + Email
- `APScheduler` background scheduler started in `RemindersConfig.ready()`
- Guard against double-start in development (checks `DISABLE_SCHEDULER` env var)
- `send_overdue_reminders()` job — queries overdue items, sends email, creates ReminderLog
- `send_reminder_email()` — Resend integration with HTML and text email body
- `python manage.py send_reminders` management command — manually triggers the
  reminder job on demand (used to test the email flow without waiting for the scheduler)

### Phase 8: System Endpoints + Docs
- `GET /health` — returns `{"status": "UP"}`
- `GET /api/evaluation` — returns candidate metadata
- drf-spectacular Swagger UI at `/api/docs/`
- OpenAPI schema at `/api/schema/`
- ReDoc at `/api/redoc/`

### Phase 9: Tests
- 56 unit tests across authentication, meetings, action items, and analysis
- All LLM API calls mocked — tests run without external services
- Tests use in-memory SQLite — no PostgreSQL required
- All 56 tests passing

### Phase 10: Deployment Config
- `Procfile` for Render/Heroku gunicorn startup
- `render.yaml` for Render auto-deployment
- Production settings with SSL, ALLOWED_HOSTS, `sslmode: require`
- WhiteNoise for static file serving
- Documentation: README, DECISIONS, AI_APPROACH, TESTING, CHANGELOG, CHECKLIST
