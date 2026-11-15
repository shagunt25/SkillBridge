import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI
from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.routes import auth, users, resume, target, analysis, prioritization, roadmap, progress, dashboard
from app.database.mongodb import ensure_indexes


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
                allowed = fetch_site in {"", "same-origin", "none"}

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
    ensure_indexes()
    yield


app = FastAPI(title="SkillBridge AI Backend", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(resume.router)
app.include_router(target.router)
app.include_router(analysis.router)
app.include_router(prioritization.router)
app.include_router(roadmap.router)
app.include_router(progress.router)
app.include_router(dashboard.router)

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


@app.get("/")
def read_root():
    return {"message": "Welcome to SkillBridge AI Backend"}
