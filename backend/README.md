# SkillBridge Backend

FastAPI backend for SkillBridge AI — handles authentication, resume analysis, and skill-gap logic.

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

**Note:** if the file-upload endpoint's browser file picker freezes (a known Chrome/Windows issue), test via `curl` instead:
```bash
curl -X POST "http://127.0.0.1:8000/resume/upload" -F "file=@C:\path\to\resume.pdf" -b cookies.txt
```

## What's Implemented

### Authentication (`/api/auth/*`)
- `POST /api/auth/signup` — create account, triggers email OTP
- `POST /api/auth/verify-email` — verify OTP, activates account
- `POST /api/auth/resend-verification-otp` — resend OTP
- `POST /api/auth/login` — returns secure HttpOnly cookie session
- `POST /api/auth/logout` — clears session
- `POST /api/auth/forgot-password` — sends password reset OTP
- `POST /api/auth/verify-reset-otp` — verifies OTP, returns short-lived reset token
- `POST /api/auth/reset-password` — changes password using reset token

### Users (`/api/users/*`)
- `GET /api/users/me` — returns currently logged-in user (requires valid session cookie)

### Resume (`/resume/*`)
- `POST /resume/upload` — **requires login**. Accepts a PDF resume, extracts text, sends it to Gemini for analysis, validates the AI response, normalizes skill names, and saves the result to MongoDB linked to the logged-in user. Re-uploading replaces the previous saved analysis (upsert).

### Target & Skill Gap Analysis (`/target/*`, `/analysis/*`)
- `POST /target/career` — **requires login**. Submit a career goal (e.g. "Backend Developer"), Gemini returns the typically required skills for that role, saved to MongoDB
- `POST /target/job` — **requires login**. Submit a full job description, Gemini extracts the skills mentioned or implied, saved to MongoDB
- `GET /analysis/skill-gap` — **requires login**. Compares the user's saved resume skills against their saved target skills using plain Python set logic (no AI involved — fast and deterministic). Requires both a resume and a target to already be saved, otherwise returns a 404 with a clear message. Returns matched, missing, and extra skills

## Important Notes

- **Passwords are hashed** with Argon2 — never stored in plain text
- **Email OTPs currently print to the terminal** (no real email service connected yet) — check your terminal after signup/forgot-password to see the code
- **Sessions use HttpOnly cookies** — the frontend does NOT need to manually store or attach any token; the browser handles it automatically as long as requests are made with credentials included
- **CORS**: currently allows `http://localhost:3000` (configurable via `FRONTEND_URL` in `.env`)
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

**Do not hardcode these values in the code** — they're already read from `.env` via `os.getenv(...)`, so switching between local and production just means setting different environment variables in each environment, no code changes needed.

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
utils/ # Security, dependencies, normalization helpers
```
