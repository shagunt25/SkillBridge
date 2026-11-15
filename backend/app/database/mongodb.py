import os
from urllib.parse import urlsplit

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
DATABASE_NAME = os.getenv("DATABASE_NAME", "").strip()


def is_valid_mongodb_uri(uri: str) -> bool:
    try:
        parsed = urlsplit(uri)
        port = parsed.port
        return (
            parsed.scheme in {"mongodb", "mongodb+srv"}
            and bool(parsed.netloc)
            and parsed.hostname is not None
            and (port is None or 0 < port <= 65535)
        )
    except ValueError:
        return False


def is_valid_database_name(name: str) -> bool:
    invalid_characters = '/\\."$*<>:|?\0'
    return (
        bool(name)
        and len(name.encode("utf-8")) <= 64
        and not any(character in name for character in invalid_characters)
    )


client = MongoClient(
    MONGODB_URI if is_valid_mongodb_uri(MONGODB_URI) else "mongodb://localhost:27017",
    serverSelectionTimeoutMS=5000,
)
db = client[
    DATABASE_NAME if is_valid_database_name(DATABASE_NAME) else "skillbridge"
]


def check_database_connection() -> None:
    client.admin.command("ping")


def ensure_indexes() -> None:
    db["users"].create_index(
        "email",
        unique=True,
    )
    db["resumes"].create_index(
        "user_email",
        unique=True,
    )
    db["targets"].create_index(
        "user_email",
        unique=True,
    )
    db["roadmaps"].create_index(
        "user_email",
        unique=True,
        partialFilterExpression={"user_email": {"$type": "string"}},
    )
    db["login_rate_limits"].create_index(
        "expires_at",
        expireAfterSeconds=0,
    )
