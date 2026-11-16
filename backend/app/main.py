import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, status
from pymongo.errors import PyMongoError
from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.routes import auth, users, resume, target, analysis, prioritization, roadmap, progress, dashboard
from app.database.mongodb import (
    DATABASE_NAME,
    MONGODB_URI,
    check_database_connection,
    ensure_indexes,
    is_valid_database_name,
    is_valid_mongodb_uri,
)
from app.services.auth_service import (
    AI_RATE_LIMIT_USER_MAX_REQUESTS,
    AI_RATE_LIMIT_WINDOW_SECONDS,
    LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS,
    LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS,
    LOGIN_RATE_LIMIT_WINDOW_SECONDS,
)
from app.services.otp_service import (
    EMAIL_BACKEND,
    OTP_EXPIRE_MINUTES,
    OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS,
    OTP_RATE_LIMIT_IP_MAX_REQUESTS,
    OTP_RATE_LIMIT_WINDOW_SECONDS,
    OTP_MAX_ATTEMPTS,
    OTP_RESEND_COOLDOWN_SECONDS,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_TIMEOUT_SECONDS,
    SMTP_USERNAME,
)
from app.routes.auth import (
    COOKIE_NAME,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    COOKIE_SECURE_VALUE_VALID,
)
from app.utils.security import JWT_EXPIRE_MINUTES, JWT_SECRET


def _normalize_origin(value: str) -> str | None:
    try:
        parsed = urlsplit(value.strip())
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None

    if (
        scheme not in {"http", "https"}
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        return None

    hostname = hostname.lower()
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"

    if port is not None and not (
        (scheme == "http" and port == 80)
        or (scheme == "https" and port == 443)
    ):
        hostname = f"{hostname}:{port}"

    return f"{scheme}://{hostname}"


def _load_frontend_origins() -> list[str]:
    configured_origins = os.getenv(
        "FRONTEND_URL",
        "http://localhost:3000",
    )
    origins = []

    for configured_origin in configured_origins.split(","):
        if not configured_origin.strip():
            continue

        origin = _normalize_origin(configured_origin)
        if origin is None:
            raise ValueError(
                "FRONTEND_URL must contain valid HTTP(S) origins."
            )
        origins.append(origin)

    if not origins:
        raise ValueError("FRONTEND_URL must contain at least one origin.")

    return list(dict.fromkeys(origins))


def _referer_origin(referer: str) -> str | None:
    try:
        parsed = urlsplit(referer)
    except ValueError:
        return None

    return _normalize_origin(f"{parsed.scheme}://{parsed.netloc}")


FRONTEND_ORIGINS = _load_frontend_origins()


def validate_configuration() -> None:
    invalid_settings = []

    if not is_valid_mongodb_uri(MONGODB_URI):
        invalid_settings.append("MONGODB_URI")
    if not is_valid_database_name(DATABASE_NAME):
        invalid_settings.append("DATABASE_NAME")
    if (
        not JWT_SECRET
        or JWT_SECRET.strip() != JWT_SECRET
        or JWT_SECRET.casefold() == "your_jwt_secret_here"
        or len(JWT_SECRET.encode("utf-8")) < 32
    ):
        invalid_settings.append("JWT_SECRET")
    if LOGIN_RATE_LIMIT_WINDOW_SECONDS <= 0:
        invalid_settings.append("LOGIN_RATE_LIMIT_WINDOW_SECONDS")
    if LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS <= 0:
        invalid_settings.append(
            "LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS"
        )
    if LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS <= 0:
        invalid_settings.append("LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS")
    if OTP_RATE_LIMIT_WINDOW_SECONDS <= 0:
        invalid_settings.append("OTP_RATE_LIMIT_WINDOW_SECONDS")
    if OTP_RATE_LIMIT_IP_MAX_REQUESTS <= 0:
        invalid_settings.append("OTP_RATE_LIMIT_IP_MAX_REQUESTS")
    if OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS <= 0:
        invalid_settings.append("OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS")
    if OTP_RESEND_COOLDOWN_SECONDS <= 0:
        invalid_settings.append("OTP_RESEND_COOLDOWN_SECONDS")
    if OTP_EXPIRE_MINUTES <= 0:
        invalid_settings.append("OTP_EXPIRE_MINUTES")
    if OTP_MAX_ATTEMPTS <= 0:
        invalid_settings.append("OTP_MAX_ATTEMPTS")
    if JWT_EXPIRE_MINUTES <= 0:
        invalid_settings.append("JWT_EXPIRE_MINUTES")
    if AI_RATE_LIMIT_WINDOW_SECONDS <= 0:
        invalid_settings.append("AI_RATE_LIMIT_WINDOW_SECONDS")
    if AI_RATE_LIMIT_USER_MAX_REQUESTS <= 0:
        invalid_settings.append("AI_RATE_LIMIT_USER_MAX_REQUESTS")
    if not COOKIE_NAME.strip():
        invalid_settings.append("COOKIE_NAME")
    if COOKIE_SAMESITE.casefold() not in {"lax", "strict", "none"}:
        invalid_settings.append("COOKIE_SAMESITE")
    if COOKIE_SAMESITE.casefold() == "none" and not COOKIE_SECURE:
        invalid_settings.append("COOKIE_SECURE")
    if not COOKIE_SECURE_VALUE_VALID:
        invalid_settings.append("COOKIE_SECURE")
    if EMAIL_BACKEND not in {"smtp", "console"}:
        invalid_settings.append("EMAIL_BACKEND")
    if SMTP_TIMEOUT_SECONDS <= 0:
        invalid_settings.append("SMTP_TIMEOUT_SECONDS")
    if not 1 <= SMTP_PORT <= 65535:
        invalid_settings.append("SMTP_PORT")
    if EMAIL_BACKEND == "smtp" and not all(
        (SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL or SMTP_USERNAME)
    ):
        invalid_settings.append("SMTP_*")

    if invalid_settings:
        settings = ", ".join(invalid_settings)
        raise RuntimeError(
            f"Missing or invalid required configuration: {settings}."
        )


class CSRFOriginMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: list[str],
    ) -> None:
        self.app = app
        self.allowed_origins = set(allowed_origins)

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if (
            scope["type"] == "http"
            and scope["method"] in {"POST", "PUT", "PATCH", "DELETE"}
        ):
            headers = Headers(scope=scope)
            host = headers.get("host")
            request_origin = (
                _normalize_origin(f"{scope['scheme']}://{host}")
                if host
                else None
            )
            trusted_origins = self.allowed_origins.copy()
            if request_origin:
                trusted_origins.add(request_origin)

            origin = headers.get("origin")
            referer = headers.get("referer")

            if origin is not None:
                source_origin = _normalize_origin(origin)
                allowed = source_origin in trusted_origins
            elif referer is not None:
                source_origin = _referer_origin(referer)
                allowed = source_origin in trusted_origins
            else:
                fetch_site = headers.get("sec-fetch-site", "").lower()
                allowed = fetch_site == "same-origin"

            if not allowed:
                response = JSONResponse(
                    status_code=403,
                    content={"detail": "Cross-origin request rejected."},
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    validate_configuration()
    try:
        check_database_connection()
    except PyMongoError as exc:
        raise RuntimeError(
            "MongoDB is unavailable during startup. Check MONGODB_URI and network access."
        ) from exc
    ensure_indexes()
    yield


app = FastAPI(title="SkillBridge AI Backend", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(resume.router)
for router in (
    target.router,
    analysis.router,
    prioritization.router,
    roadmap.router,
    progress.router,
    dashboard.router,
):
    app.include_router(router, prefix="/api")
    app.include_router(router, include_in_schema=False)

app.add_middleware(
    CSRFOriginMiddleware,
    allowed_origins=FRONTEND_ORIGINS,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)


@app.get("/health/live", tags=["health"])
def liveness():
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
def readiness():
    try:
        check_database_connection()
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc

    return {"status": "ready"}


@app.get("/")
def read_root():
    return {"message": "Welcome to SkillBridge AI Backend"}
