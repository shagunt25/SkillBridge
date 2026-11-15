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

### 6. Test the API
Visit http://127.0.0.1:8000/docs for interactive API documentation (Swagger UI) â€” every endpoint can be tested directly from there.

To run the automated backend tests from the `backend` directory:
```bash
python -m pytest -q
```

**Note:** if the file-upload endpoint's browser file picker freezes (a known Chrome/Windows issue), test via `curl` instead:
```bash
curl -X POST "http://127.0.0.1:8000/resume/upload" -F "file=@C:\path\to\resume.pdf" -b cookies.txt
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

### Resume (`/resume/*`)
- `POST /resume/upload` â€” **requires login**. Accepts a PDF resume, extracts text, sends it to Gemini for analysis, validates the AI response, normalizes skill names, and saves the result to MongoDB linked to the logged-in user. Re-uploading replaces the previous saved analysis (upsert).

- Resume uploads are limited to 5 MB, 20 pages, and 50,000 extracted text characters. Synchronous PDF extraction, Gemini requests, and MongoDB writes run in a worker thread so they do not block the async request loop.

## OTP Rate Limiting

Both `POST /api/auth/resend-verification-otp` and `POST /api/auth/forgot-password` enforce a cooldown between consecutive requests, controlled by `OTP_RESEND_COOLDOWN_SECONDS` in `.env` (default: 60 seconds). Requesting a new code before the cooldown expires returns a `429 Too Many Requests` with a message telling the user how many seconds remain.

## Session Invalidation on Password Change

JWTs include an `iat` (issued-at) claim. Whenever a password is changed â€” via `POST /api/auth/reset-password` (forgot-password flow) or `POST /api/users/me/change-password` (logged-in flow) â€” the user's `password_changed_at` timestamp is updated in MongoDB. `get_current_user()` compares this against each token's `iat` on every request; any token issued *before* the most recent password change is rejected, forcing re-login. This prevents an old, possibly compromised session from remaining valid after a password change.

### Target & Skill Gap Analysis (`/target/*`, `/analysis/*`)
- `POST /target/career` — **requires login**. Submit a career goal (e.g. "Backend Developer"), Gemini returns the typically required skills for that role, saved to MongoDB
- `POST /target/job` — **requires login**. Submit a full job description, Gemini extracts the skills mentioned or implied, saved to MongoDB
- Submitting a genuinely different target clears the existing roadmap and progress. Equivalent roles and skill sets are compared case-insensitively and preserve the roadmap.
- `GET /analysis/skill-gap` — **requires login**. Compares the user's saved resume skills against their saved target skills using plain Python set logic (no AI involved — fast and deterministic). Requires both a resume and a target to already be saved, otherwise returns a 404 with a clear message. Returns matched, missing, and extra skills
- Resume, target, and dashboard skill comparisons normalize whitespace, punctuation, and common aliases such as `JS`/`JavaScript` and `Node.js`/`Node JS`.

### Roadmap & Progress (`/roadmap/*`, `/progress/*`)
- `POST /roadmap/generate` - generates or refreshes the authenticated user's learning roadmap.
- `GET /progress` - retrieves the roadmap and completion percentage.
- `PATCH /progress/update` - updates a skill and its subtopics.
- `PATCH /progress/subtopic/update` - updates one subtopic and recalculates its skill status.
- Progress writes are retried when another request changes the roadmap at the same time. If contention persists, the API returns `409 Conflict`; refresh the progress and retry.

## Important Notes

- **Passwords are hashed** with Argon2 â€” never stored in plain text
- **Email delivery** uses the configured backend. With `EMAIL_BACKEND=console`, OTPs print to the terminal; use `EMAIL_BACKEND=smtp` to send them through Gmail SMTP.
- **Sessions use HttpOnly cookies** â€” the frontend does NOT need to manually store or attach any token; the browser handles it automatically as long as requests are made with credentials included
- **CORS and CSRF**: credentialed CORS is restricted to the exact comma-separated origins in `FRONTEND_URL`. Unsafe requests validate `Origin` or `Referer`, with Fetch Metadata as a fallback; cross-site mutations are rejected.


- **For frontend developers:** when calling these endpoints from React, include `credentials: 'include'` in fetch requests or `withCredentials: true` in Axios requests; otherwise, the browser won't send or receive the session cookie.
- **Authentication is required** for resume uploads, target submissions, and skill-gap analysis. The frontend should ensure the user is logged in or handle `401` responses gracefully.
- **Skill-gap analysis requires both a saved resume and a saved target.** Guide users through resume upload and target selection before displaying the results.
- **Gemini API has rate limits** on the free tier. Simultaneous testing may result in `429` errors; this is expected.

## Cookie Configuration — Local vs Production

- **For frontend developers**: when calling these endpoints from React, include `credentials: 'include'` (fetch) or `withCredentials: true` (axios) on every request — otherwise the browser won't send/receive the session cookie, and login will silently fail to persist
- **Resume uploads, target submissions, and skill-gap analysis all require authentication** — the frontend must ensure the user is logged in before showing these features, or handle the resulting 401 gracefully
- **Skill gap analysis requires both a resume and a target to already be saved** — the frontend should guide the user through resume upload and target selection before attempting to show the skill gap view
- **Gemini API has rate limits** on the free tier — if multiple teammates test simultaneously, you may hit `429` errors; this is expected and not a bug

## Cookie Configuration — Local vs Production

Look closely at these two lines in your `.env` file:
```
Look closely at these two lines in your `.env` file:

COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

These settings are correct for local development. Browsers will only accept a `SameSite=None` cookie if it's sent over HTTPS (`Secure=True`). Since you're testing locally on plain HTTP (`localhost`), using `lax` and `false` is the only way to make login actually work on your laptop.

**This will break in production.** Because our architecture hosts the React frontend on Vercel and the FastAPI backend on a separate Render domain, the browser will block the auth cookie unless `COOKIE_SAMESITE=none` and `COOKIE_SECURE=true` are configured (via environment variables in each platform's dashboard) once we deploy.

**Do not hardcode these values in the code** â€” they're already read from `.env` via `os.getenv(...)`, so switching between local and production just means setting different environment variables in each environment, no code changes needed.

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
