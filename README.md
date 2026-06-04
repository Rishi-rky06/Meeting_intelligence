# Meeting Intelligence Service

An AI-powered backend service that helps teams capture insights, action items, decisions, and follow-ups from meeting transcripts.

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

## Local Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 14+

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/meeting-intelligence.git
cd meeting-intelligence
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
| `CANDIDATE_NAME` | No | Your name for /api/evaluation | `Koushik Reddy Yeredla` |
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

1. Push your code to GitHub (make sure `.env` is in `.gitignore`)
2. Create a new **Web Service** on Render pointing to your repo
3. Set environment variables in the Render dashboard
4. Add a **PostgreSQL** database on Render and set the DB connection variables
5. Render auto-deploys on every push to `main`

Build command:
```
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

Start command:
```
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

---

## API Documentation

Swagger UI: `/api/docs/`
OpenAPI schema: `/api/schema/`
ReDoc: `/api/redoc/`
