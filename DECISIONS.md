# Technical Decisions

## 1. Database: PostgreSQL

**Chosen:** PostgreSQL via `psycopg2-binary`

**Why:** PostgreSQL's `JSONField` support is first-class (used for `participants`, `citations`, `raw_response`). It handles UUID primary keys natively, supports full ACID transactions needed for the atomic analysis persistence step, and is available as a managed service on Render with zero configuration.

**Alternatives considered:**
- **SQLite** — zero-ops but not suitable for production (file locking, no concurrent writes)
- **MongoDB** — good fit for JSON-heavy data but adds operational complexity and loses relational integrity between meetings, analysis items, and citations

**Trade-offs:** Requires a running Postgres instance for local development (mitigated by SQLite fallback in `testing.py`).

---

## 2. Authentication: Custom JWT with PyJWT

**Chosen:** Hand-rolled JWT using PyJWT only

**Why:** The assignment explicitly required custom JWT. Using `PyJWT` directly gives full control over token claims, expiry logic, and algorithm selection with no magic. Middleware injects `request.user_id` so any view can access the authenticated user without coupling to DRF's auth backend system.

**Alternatives considered:**
- **djangorestframework-simplejwt** — excellent library but prohibited by requirements
- **Session-based** — simpler but stateful (requires server-side session store), not suitable for a stateless REST API

**Trade-offs:** No built-in token revocation. Logout is client-side only (tokens remain valid until expiry). A Redis-backed denylist could address this but was out of scope.

---

## 3. AI Provider: Groq (Llama 3.3 70B)

**Chosen:** `llama-3.3-70b-versatile` via Groq, using the official `openai` Python SDK pointed at Groq's OpenAI-compatible base URL (`https://api.groq.com/openai/v1`).

**Why:** Groq offers a genuinely generous free tier (thousands of requests/day) with very fast inference, and exposes an OpenAI-compatible API — so the same `openai` SDK is reused with only a different base URL. `llama-3.3-70b-versatile` is a large (70B) model that follows the strict JSON-with-citations grounding prompt reliably. A direct provider key avoids the heavy shared-pool throttling seen on proxy free tiers. Using the OpenAI protocol keeps the integration portable — switching providers or upgrading is a one-line env-var change.

**Alternatives considered:**
- **OpenRouter (free models)** — convenient single API for many models, but the keyless free tier routes through a shared, heavily rate-limited provider pool (frequent `429`s), making it unreliable for evaluation
- **Anthropic Claude** — excellent structured output, but a paid-only API
- **OpenAI GPT-4o (direct)** — comparable quality but paid
- **Google Gemini (direct)** — also a strong free tier; Groq was chosen for speed and the drop-in OpenAI-compatible SDK

**Trade-offs:** Groq's free tier still has per-minute/daily rate limits, so heavy bursts can return a `429`. This is handled gracefully (returns `ANALYSIS_FAILED` rather than crashing), and the `GROQ_BASE_URL`/`GROQ_MODEL` env vars allow switching to a paid tier or another provider with no code change.

---

## 4. Email Integration: Resend

**Chosen:** Resend via the `resend` Python SDK

**Why:** Resend has a clean, minimal API. The Python SDK wraps it in two lines. It is developer-friendly, has a free tier, and delivers transactional email reliably. No complex setup required.

**Alternatives considered:**
- **SendGrid** — more features but heavier setup and higher pricing
- **Mailgun** — similar simplicity but Resend's DX is cleaner
- **Slack Webhook** — easier to set up but email better fits the "action item reminder" use case

**Trade-offs:** Resend requires domain verification in production. The `RESEND_FROM_EMAIL` must use a verified domain.

---

## 5. Scheduler: APScheduler

**Chosen:** `APScheduler` with `BackgroundScheduler`

**Why:** APScheduler runs in-process alongside the Django/gunicorn workers. No separate process or queue infrastructure is needed. It supports `IntervalTrigger`, handles timezone-aware execution, and the `max_instances=1` guard prevents overlapping runs.

**Alternatives considered:**
- **Celery + Redis** — production-grade but requires a separate broker, separate worker process, and additional infrastructure
- **Django-Q** — simpler than Celery but still needs a message broker
- **node-cron equivalent (django-crontab)** — requires OS-level cron access, not available on Render

**Trade-offs:** APScheduler runs per-dyno — if you scale to multiple Render instances, each dyno runs the job independently. A distributed lock (Redis) would be needed for true single-execution at scale. Acceptable for this assignment scope.

---

## 6. Project Structure: Feature-based Apps

**Chosen:** `apps/authentication`, `apps/meetings`, `apps/analysis`, `apps/action_items`, `apps/reminders`

**Why:** Feature-based structure groups all related code (model, view, serializer, test) together. This keeps each domain self-contained and easy to navigate.

**Alternatives considered:**
- **Flat structure** — simpler for small projects but becomes a mess as the codebase grows
- **Monolithic app** — single `models.py` and `views.py` — impossible to maintain at any scale

**Trade-offs:** Slightly more boilerplate (`apps.py`, `__init__.py` per app) but the organizational benefit outweighs this.

---

## 7. API Response Format: Unified Envelope

**Chosen:** Every response returns `{ traceId, success, data }` or `{ traceId, success, error }`.

**Why:** Consistent response format means API clients never need to special-case error detection. The trace ID in every response allows correlating frontend errors to backend logs instantly.

**Implementation:** `core/response.py` provides `success_response()` and `error_response()`. The global exception handler in `core/exceptions.py` ensures even unhandled exceptions follow the same format.
