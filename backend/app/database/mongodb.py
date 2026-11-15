import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]


def ensure_indexes() -> None:
    db["users"].create_index(
        "email",
        unique=True,
        name="uq_users_email",
    )
    db["resumes"].create_index(
        "user_email",
        unique=True,
        name="uq_resumes_user_email",
    )
    db["targets"].create_index(
        "user_email",
        unique=True,
        name="uq_targets_user_email",
    )
    db["roadmaps"].create_index(
        "user_email",
        unique=True,
        name="uq_roadmaps_user_email",
    )
