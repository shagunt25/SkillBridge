# SkillBridge Backend

FastAPI backend for SkillBridge AI â€” handles authentication, resume analysis, and skill-gap logic.

## Tech Stack
- Python 3.10+
- FastAPI + Uvicorn
- MongoDB (via PyMongo)
- Google Gemini API (resume analysis, target skill mapping)
- PyMuPDF (PDF text extraction)
- JWT + HttpOnly cookies (authentication)

## Setup Instructions

### 1. Navigate to the backend folder
```bash
cd backend
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate      # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements-dev.txt
```

This installs the runtime dependencies from `requirements.txt` along with the test tools. For a runtime-only install, use `pip install -r requirements.txt`.

### 4. Create your own .env file
Copy `.env.example` to `.env`, then fill in your own values:
```bash
copy .env.example .env        # Windows
cp .env.example .env           # Mac/Linux
```

You'll need:
- A MongoDB connection string (ask Sagun for the shared cluster URI, or create your own free MongoDB Atlas cluster for local testing)
- A JWT secret (generate one: `python -c "import secrets; print(secrets.token_hex(32))"`)
- A Gemini API key (get one free at https://aistudio.google.com/app/apikey)

### Configure OTP email

For local development, `EMAIL_BACKEND=console` prints OTPs to the backend terminal. To send real email using a dedicated Gmail account, enable 2-Step Verification and create a Google App Password. In `backend/.env`, set:

```env
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-project-mailbox@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-project-mailbox@gmail.com
SMTP_FROM_NAME=SkillBridge
```

Paste the App Password without spaces. Keep it only in `backend/.env` locally and in your deployment platform's secret settings when deploying. Do not put it in source code, `.env.example`, or a Docker image. If signup email delivery fails after account creation, the account remains unverified; fix the SMTP settings and use the resend-verification endpoint.

### 5. Run the server
```bash
uvicorn app.main:app --reload
```

Server runs at http://127.0.0.1:8000

On startup, the backend creates unique indexes for user emails and each user's resume, target, and roadmap. If an existing database already contains duplicate values for those fields, index creation will fail; remove or reconcile duplicates before starting the updated backend.

Startup requires a valid MongoDB URI, database name, and a non-placeholder JWT secret with at least 32 bytes. MongoDB connectivity is checked before the application starts; Gemini and Tavily keys remain optional for features that use them.

The backend uses MongoDB transactions for account deletion, target changes, email verification, and password reset. Use a replica set or sharded MongoDB deployment; MongoDB Atlas satisfies this requirement.

`GET /health/live` reports whether the process is running. `GET /health/ready` pings MongoDB and returns `503 Service Unavailable` when the database cannot be reached.

### 6. Test the API
Visit http://127.0.0.1:8000/docs for interactive API documentation (Swagger UI) â€” every endpoint can be tested directly from there.

To run the automated backend tests from the `backend` directory:
```bash
python -m pytest -q --cov=app --cov-report=term-missing
```

The automated suite uses `mongomock` and mocked AI/email providers. It does not replace a deployment-level integration check against a replica-set MongoDB or real provider credentials.

**Note:** if the file-upload endpoint's browser file picker freezes (a known Chrome/Windows issue), test via `curl` instead:
```bash
curl -X POST "http://127.0.0.1:8000/api/resume/upload" -F "file=@C:\path\to\resume.pdf" -b cookies.txt
```

## What's Implemented

### Authentication (`/api/auth/*`)
- `POST /api/auth/signup` â€” create account, triggers email OTP
- `POST /api/auth/verify-email` â€” verify OTP, activates account
- `POST /api/auth/resend-verification-otp` â€” resend OTP (rate-limited â€” see OTP Rate Limiting section below)
- `POST /api/auth/login` â€” returns secure HttpOnly cookie session
- `POST /api/auth/logout` â€” clears session
- `POST /api/auth/forgot-password` â€” sends password reset OTP (rate-limited â€” see OTP Rate Limiting section below)
- `POST /api/auth/verify-reset-otp` â€” verifies OTP, returns short-lived reset token
- `POST /api/auth/reset-password` â€” changes password using reset token. Invalidates any existing login sessions.

### Users (`/api/users/*`)
- `GET /api/users/me` â€” returns currently logged-in user (requires valid session cookie)
- `POST /api/users/me/change-password` â€” **requires login**. Change password while logged in, using your current password (not OTP-based, unlike forgot-password). Requires `old_password` and `new_password` in the body. Invalidates any existing login sessions â€” you'll need to log in again afterward.
- `DELETE /api/users/me` â€” **requires login**. Permanently deletes the logged-in user's account and associated resume, target, roadmap, OTP, and password-reset records.

### Resume (`/api/resume/*`)
- `POST /api/resume/upload` â€” **requires login**. Accepts a PDF resume, extracts text, sends it to Gemini for analysis, validates the AI response, normalizes skill names, and saves the result to MongoDB linked to the logged-in user. Re-uploading replaces the previous saved analysis (upsert).

- Resume uploads are limited to 5 MB, 20 pages, and 50,000 extracted text characters. Synchronous PDF extraction, Gemini requests, and MongoDB writes run in a worker thread so they do not block the async request loop.

## OTP Rate Limiting

Both `POST /api/auth/resend-verification-otp` and `POST /api/auth/forgot-password` enforce an atomic cooldown between consecutive requests, controlled by `OTP_RESEND_COOLDOWN_SECONDS` in `.env` (default: 60 seconds). Account-specific cooldown and delivery outcomes use generic responses to avoid revealing whether an account exists.

`POST /api/auth/login` also limits failed attempts using MongoDB-backed counters: 5 per email/IP pair and 30 per IP in each 15-minute window by default. Configure the limits with `LOGIN_RATE_LIMIT_WINDOW_SECONDS`, `LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS`, and `LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS`. A blocked login returns `429 Too Many Requests` and a `Retry-After` header. The counters expire automatically through a MongoDB TTL index.

Verification and reset-code requests are also limited to 10 per IP and 5 per email per hour by default, configurable with `OTP_RATE_LIMIT_WINDOW_SECONDS`, `OTP_RATE_LIMIT_IP_MAX_REQUESTS`, and `OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS`. An IP limit returns `429`; an email limit returns the same generic response used for unknown accounts. All counters expire through MongoDB TTL indexes.

Gemini-backed operations are limited to 20 requests per authenticated user per hour by default (`AI_RATE_LIMIT_WINDOW_SECONDS` and `AI_RATE_LIMIT_USER_MAX_REQUESTS`). Roadmaps are limited to 12 subtopics per skill and at most five Tavily searches per generation.

The login and OTP IP limiters use the request's client IP. When running behind a reverse proxy, configure Uvicorn's forwarded-header trust only for that trusted proxy so IP-based limits use the actual client address.

## Session Invalidation on Password Change

JWTs include a session-version claim. Whenever a password is changed via `POST /api/auth/reset-password` or `POST /api/users/me/change-password`, the user's `session_version` increments. `get_current_user()` compares the claim against the stored version on each request, rejecting sessions issued before the password change.

### Target & Skill Gap Analysis (`/api/target/*`, `/api/analysis/*`)
- `POST /api/target/career` — **requires login**. Submit a career goal (e.g. "Backend Developer"), Gemini returns the typically required skills for that role, saved to MongoDB
- `POST /api/target/job` — **requires login**. Submit a full job description, Gemini extracts the skills mentioned or implied, saved to MongoDB
- Submitting a genuinely different target clears the existing roadmap and progress. Equivalent roles and skill sets are compared case-insensitively and preserve the roadmap.
- `GET /api/analysis/skill-gap` — **requires login**. Compares the user's saved resume skills against their saved target skills using plain Python set logic (no AI involved — fast and deterministic). Requires both a resume and a target to already be saved, otherwise returns a 404 with a clear message. Returns matched, missing, and extra skills
- `GET /api/analysis/prioritized-skills` — **requires login**. Ranks the missing skills for the user's target role.
- Resume, target, and dashboard skill comparisons normalize whitespace, punctuation, and common aliases such as `JS`/`JavaScript` and `Node.js`/`Node JS`.

### Roadmap & Progress (`/api/roadmap/*`, `/api/progress/*`)
- `POST /api/roadmap/generate` - generates or refreshes the authenticated user's learning roadmap.
- `GET /api/progress` - retrieves the roadmap and completion percentage.
- `PATCH /api/progress/update` - updates a skill and its subtopics.
- `PATCH /api/progress/subtopic/update` - updates one subtopic and recalculates its skill status.
- Progress writes are retried when another request changes the roadmap at the same time. If contention persists, the API returns `409 Conflict`; refresh the progress and retry.

### Dashboard (`/api/dashboard`)
- `GET /api/dashboard` — **requires login**. Returns the user's profile, skill match summary, roadmap, and overall progress.

The canonical API prefix is `/api`. The previous unprefixed target, analysis, roadmap, progress, and dashboard paths remain available as undocumented compatibility aliases; new clients should use the `/api/...` paths.

## Cookie Configuration — Local vs Production

For local HTTP development, use:

```env
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

Cross-site cookies require `COOKIE_SAMESITE=none` and `COOKIE_SECURE=true`; startup rejects `SameSite=None` without Secure. Set production values through the deployment environment, not source code.

## Important Notes

- Passwords are hashed with Argon2 and are never stored in plain text.
- With `EMAIL_BACKEND=console`, OTPs are printed to the backend terminal. SMTP mode requires valid credentials at startup.
- Browser clients must send requests with `credentials: "include"` or Axios `withCredentials: true`.
- Credentialed CORS is restricted to exact origins in `FRONTEND_URL`. Mutating requests must include an allowed `Origin` or `Referer`, or same-origin Fetch Metadata.
- Resume upload, target submission, and analysis endpoints require authentication. Skill-gap analysis requires both a saved resume and target.

## Folder Structure
```
backend/
app/
main.py # App entry point, wires all routers
routes/ # API endpoints (auth, users, resume, target, analysis)
schemas/ # Request/response validation (Pydantic)
services/ # Business logic (auth, otp, gemini, pdf, resume, target, analysis)
models/ # Database document shapes
database/ # MongoDB connection
utils/ # Security helpers, authentication dependencies, and normalization
