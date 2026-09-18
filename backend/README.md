# SkillBridge Backend

FastAPI backend for SkillBridge AI — handles authentication, resume analysis, and skill-gap logic.

## Tech Stack
- Python 3.10+
- FastAPI + Uvicorn
- MongoDB (via PyMongo)
- Google Gemini API (resume analysis)
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
pip install -r requirements.txt
```

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

### 5. Run the server
```bash
uvicorn app.main:app --reload
```

Server runs at http://127.0.0.1:8000

### 6. Test the API
Visit http://127.0.0.1:8000/docs for interactive API documentation (Swagger UI) — every endpoint can be tested directly from there.

## What's Implemented

### Authentication (`/api/auth/*`)
- `POST /api/auth/signup` — create account, triggers email OTP
- `POST /api/auth/verify-email` — verify OTP, activates account
- `POST /api/auth/resend-verification-otp` — resend OTP (rate-limited — see OTP Rate Limiting section below)
- `POST /api/auth/login` — returns secure HttpOnly cookie session
- `POST /api/auth/logout` — clears session
- `POST /api/auth/forgot-password` — sends password reset OTP (rate-limited — see OTP Rate Limiting section below)
- `POST /api/auth/verify-reset-otp` — verifies OTP, returns short-lived reset token
- `POST /api/auth/reset-password` — changes password using reset token. Invalidates any existing login sessions.

### Users (`/api/users/*`)
- `GET /api/users/me` — returns currently logged-in user (requires valid session cookie)
- `POST /api/users/me/change-password` — **requires login**. Change password while logged in, using your current password (not OTP-based, unlike forgot-password). Requires `old_password` and `new_password` in the body. Invalidates any existing login sessions — you'll need to log in again afterward.
- `DELETE /api/users/me` — **requires login**. Permanently deletes the logged-in user's account. Note: currently only deletes the user document itself — does not yet clean up associated data in other collections (known limitation, will need addressing once resume/target data collections are merged in).

### Resume (`/resume/*`)
- `POST /resume/upload` — upload PDF resume, extracts text, analyzes with Gemini AI, returns structured skills/education/experience/projects

## OTP Rate Limiting

Both `POST /api/auth/resend-verification-otp` and `POST /api/auth/forgot-password` enforce a cooldown between consecutive requests, controlled by `OTP_RESEND_COOLDOWN_SECONDS` in `.env` (default: 60 seconds). Requesting a new code before the cooldown expires returns a `429 Too Many Requests` with a message telling the user how many seconds remain.

## Session Invalidation on Password Change

JWTs include an `iat` (issued-at) claim. Whenever a password is changed — via `POST /api/auth/reset-password` (forgot-password flow) or `POST /api/users/me/change-password` (logged-in flow) — the user's `password_changed_at` timestamp is updated in MongoDB. `get_current_user()` compares this against each token's `iat` on every request; any token issued *before* the most recent password change is rejected, forcing re-login. This prevents an old, possibly compromised session from remaining valid after a password change.

## Important Notes

- **Passwords are hashed** with Argon2 — never stored in plain text
- **Email OTPs currently print to the terminal** (no real email service connected yet) — check your terminal after signup/forgot-password to see the code
- **Sessions use HttpOnly cookies** — the frontend does NOT need to manually store or attach any token; the browser handles it automatically as long as requests are made with credentials included
- **CORS**: currently allows `http://localhost:3000` (configurable via `FRONTEND_URL` in `.env`)
- **For frontend developers**: when calling these endpoints from React, include `credentials: 'include'` (fetch) or `withCredentials: true` (axios) on every request — otherwise the browser won't send/receive the session cookie, and login will silently fail to persist

## Cookie Configuration — Local vs Production

Look closely at these two lines in your `.env` file:
```
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

These settings are correct for local development. Browsers will only accept a `SameSite=None` cookie if it's sent over HTTPS (`Secure=True`). Since you're testing locally on plain HTTP (`localhost`), using `lax` and `false` is the only way to make login actually work on your laptop.

**This will break in production.** Because our architecture hosts the React frontend on Vercel and the FastAPI backend on a separate Render domain, the browser will block the auth cookie unless `COOKIE_SAMESITE=none` and `COOKIE_SECURE=true` are configured (via environment variables in each platform's dashboard) once we deploy.

**Do not hardcode these values in the code** — they're already read from `.env` via `os.getenv(...)`, so switching between local and production just means setting different environment variables in each environment, no code changes needed.

## Folder Structure
```
backend/
app/
main.py # App entry point, wires all routers
routes/ # API endpoints
schemas/ # Request/response validation (Pydantic)
services/ # Business logic
models/ # Database document shapes
database/ # MongoDB connection
utils/ # Security helpers (hashing, JWT, auth dependency)
```