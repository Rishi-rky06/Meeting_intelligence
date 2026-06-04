# Meeting Intelligence Service

An AI-powered backend service that helps teams capture insights, action items, decisions, and follow-ups from meeting transcripts.

Give it a meeting transcript and it uses an LLM to produce a **summary, action items, decisions, and follow-ups** — where **every insight is backed by a citation** pointing to the exact line in the transcript it came from. Action items are tracked, overdue ones are detected automatically, and a background job emails reminders.

## Live Demo

| Resource | URL |
|----------|-----|
| Live API | https://meeting-intelligence-nj4u.onrender.com |
| Swagger / API docs | https://meeting-intelligence-nj4u.onrender.com/api/docs/ |
| Health check | https://meeting-intelligence-nj4u.onrender.com/health |
| Evaluation info | https://meeting-intelligence-nj4u.onrender.com/api/evaluation |

> Note: the API is hosted on Render's free tier, which sleeps after ~15 min of inactivity. The **first request may take 30–50 seconds** to wake the service; it's fast after that.

## Features

- **Custom JWT authentication** — register, login, refresh, logout (built with PyJWT, no auth libraries)
- **Meeting management** — store meetings with full transcripts (pagination + owner scoping)
- **AI meeting analysis** — summary, action items, decisions, follow-ups, each with transcript **citations**
- **Hallucination prevention** — strict grounding prompt + post-processing that drops any uncited insight
- **Action item tracking** — create, update status (PENDING → IN_PROGRESS → COMPLETED), filter
- **Overdue detection** — flags items past their due date that aren't completed
- **Scheduled reminders** — background job (APScheduler) emails overdue assignees via Resend
- **Production basics** — unified response envelope, request trace IDs, structured logging, global error handling, input validation, CORS, Swagger docs

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 5.1 + Django REST Framework |
| Database | PostgreSQL |
| AI | Llama 3.3 70B via Groq (using `openai` SDK) |
| Auth | Custom JWT using PyJWT |
| Scheduler | APScheduler |
| Email | Resend |
| API Docs | drf-spectacular (Swagger/OpenAPI) |
| Config | python-decouple |
| Deployment | Render |

---

## Project Structure

The project uses a **feature-based layout** — each domain is a self-contained Django app holding its own models, views, serializers, urls, and tests.

```
meeting_intelligence/
├── config/              # Project config
│   ├── settings/        # Split settings: base / development / production / testing
│   ├── urls.py          # Root URL routing
│   └── wsgi.py
├── core/                # Shared infrastructure used by all apps
│   ├── middleware.py    # Trace ID middleware
│   ├── response.py      # Unified success/error response helpers
│   ├── exceptions.py    # Global exception handler
│   ├── pagination.py    # Paginated response wrapper
│   ├── permissions.py   # JWT permission class
│   └── validators.py    # Reusable validators
└── apps/                # One app per feature
    ├── authentication/  # Custom User + JWT (register/login/refresh/logout)
    ├── meetings/        # Meeting + transcript storage
    ├── analysis/        # AI analysis (Groq) + citations  (services/ holds prompt + LLM logic)
    ├── action_items/    # Action items, status tracking, overdue detection
    └── reminders/       # APScheduler job + Resend email integration
```

---

## Local Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 14+

### 1. Clone the repository

```bash
git clone https://github.com/Rishi-rky06/Meeting_intelligence.git
cd Meeting_intelligence
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values (see [Environment Variables](#environment-variables) below).

### 5. Create the PostgreSQL database

```sql
CREATE DATABASE meeting_intelligence;
```

### 6. Run migrations

```bash
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py migrate
```

### 7. Start the server

```bash
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py runserver
```

The API is now available at `http://localhost:8000`.
Swagger docs: `http://localhost:8000/api/docs/`

---

## Running Tests

```bash
DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py test apps.authentication apps.meetings apps.action_items apps.analysis --verbosity=2
```

Tests use an in-memory SQLite database — no PostgreSQL required for testing.

### Triggering reminders manually

The reminder job normally runs every 30 minutes on a schedule. To trigger it **immediately** (e.g. to test the email flow), run:

```bash
python manage.py send_reminders
```

This finds all overdue action items, emails their assignees via Resend, and records each attempt in the `ReminderLog` table.

---

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DJANGO_SETTINGS_MODULE` | Yes | Settings module to use | `config.settings.development` |
| `SECRET_KEY` | Yes | Django secret key | random 50-char string |
| `JWT_SECRET_KEY` | Yes | JWT signing key | random 50-char string |
| `DB_NAME` | Yes | PostgreSQL database name | `meeting_intelligence` |
| `DB_USER` | Yes | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | Yes | PostgreSQL password | `yourpassword` |
| `DB_HOST` | Yes | Database host | `localhost` |
| `DB_PORT` | No | Database port | `5432` |
| `GROQ_API_KEY` | Yes | Groq API key | `gsk_...` |
| `GROQ_MODEL` | No | Groq model ID | `llama-3.3-70b-versatile` |
| `GROQ_BASE_URL` | No | Groq OpenAI-compatible base URL | `https://api.groq.com/openai/v1` |
| `RESEND_API_KEY` | Yes | Resend API key for emails | `re_...` |
| `RESEND_FROM_EMAIL` | Yes | Sender email address | `reminders@yourdomain.com` |
| `SCHEDULER_INTERVAL_MINUTES` | No | Reminder job frequency | `30` |
| `CANDIDATE_NAME` | No | Your name for /api/evaluation | `Sheela Rishikesh Yadav` |
| `CANDIDATE_EMAIL` | No | Your email for /api/evaluation | `you@example.com` |
| `REPOSITORY_URL` | No | GitHub repo URL | `https://github.com/...` |
| `DEPLOYED_URL` | No | Render deployment URL | `https://...onrender.com` |
| `ALLOWED_HOSTS` | Prod only | Comma-separated allowed hosts | `yourapp.onrender.com` |

---

## API Usage Examples

### Authentication

**Register**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "password": "Str0ng!Pass"}'
```

**Login**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "Str0ng!Pass"}'
```

### Meetings

**Create a meeting with transcript**
```bash
curl -X POST http://localhost:8000/api/meetings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "title": "Sprint Planning",
    "participants": ["alice@example.com", "bob@example.com"],
    "meetingDate": "2026-05-20T10:00:00Z",
    "transcript": [
      {"timestamp": "00:10", "speaker": "John", "text": "We should launch next Friday."},
      {"timestamp": "00:20", "speaker": "Alice", "text": "I will prepare release notes."}
    ]
  }'
```

**List meetings**
```bash
curl http://localhost:8000/api/meetings/?page=1&pageSize=10 \
  -H "Authorization: Bearer <access_token>"
```

### AI Analysis

**Analyze a meeting**
```bash
curl -X POST http://localhost:8000/api/meetings/<meeting_id>/analyze \
  -H "Authorization: Bearer <access_token>"
```

### Action Items

**Get overdue items**
```bash
curl http://localhost:8000/api/action-items/overdue \
  -H "Authorization: Bearer <access_token>"
```

**Update status**
```bash
curl -X PATCH http://localhost:8000/api/action-items/<item_id>/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"status": "COMPLETED"}'
```

---

## Deployment to Render

This repo includes a **Render Blueprint** ([`render.yaml`](render.yaml)) that provisions everything automatically — the web service **and** a free PostgreSQL database, with the database connection variables auto-injected.

1. Push your code to GitHub (`.env` is gitignored, so secrets stay local).
2. On Render: **New → Blueprint**, and select this repository.
3. Render reads `render.yaml` and creates the web service + database.
4. When prompted, enter the two secret values (`GROQ_API_KEY`, `RESEND_API_KEY`) — everything else is set automatically.
5. Render builds and deploys; future pushes to `main` auto-deploy.

Under the hood the Blueprint runs:

- **Build:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- **Start:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

Production settings (`config/settings/production.py`) enable SSL, require a database SSL connection, and serve static files via WhiteNoise.

---

## API Documentation

Swagger UI: `/api/docs/`
OpenAPI schema: `/api/schema/`
ReDoc: `/api/redoc/`
