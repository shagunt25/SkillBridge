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
- `POST /api/auth/resend-verification-otp` — resend OTP
- `POST /api/auth/login` — returns secure