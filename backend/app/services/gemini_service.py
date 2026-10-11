import os
import json

from google import genai
from dotenv import load_dotenv
from fastapi import HTTPException, status
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.schemas.resume import ResumeAnalysis

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.6-flash"

EXTRACTION_PROMPT = """
You are analyzing a resume. Extract the candidate's information and return ONLY valid JSON, no markdown, no explanation, no code fences.

Return this exact structure:
{
  "skills": [{"name": "string", "level": "Beginner|Intermediate|Advanced"}],
  "education": [{"degree": "string", "institution": "string", "year": "string"}],
  "experience": [{"role": "string", "company": "string", "duration": "string"}],
  "projects": [{"title": "string", "description": "string"}]
}

If a section has no information, return an empty list for it.
Do not invent information that isn't in the resume text.

Resume text:
"""


def is_retryable_gemini_error(exc: Exception) -> bool:
    """Retry only errors that are likely to be temporary."""
    code = getattr(exc, "code", None)
    if code is None:
        code = getattr(exc, "status_code", None)

    try:
        code = int(code)
    except (TypeError, ValueError):
        code = None

    if code in {429, 500, 502, 503, 504}:
        return True

    error_name = type(exc).__name__.lower()

    retryable_names = (
        "toomanyrequests",
        "resourceexhausted",
        "serviceunavailable",
        "internalservererror",
        "deadlineexceeded",
    )

    return any(name in error_name for name in retryable_names)


@retry(
    retry=retry_if_exception(is_retryable_gemini_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=8),
    reraise=True,
)
def generate_resume_content(resume_text: str):
    """Make at most three attempts for retryable Gemini errors."""
    return client.models.generate_content(
        model=MODEL_NAME,
        contents=EXTRACTION_PROMPT + resume_text,
    )


def analyze_resume_text(resume_text: str) -> dict:
    try:
        response = generate_resume_content(resume_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API request failed after retries, if applicable: {str(e)}",
        ) from e

    raw_text = (response.text or "").strip()

    if not raw_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an empty response. Please try again.",
        )

    # Remove optional Markdown code fences.
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        raw_text = "\n".join(lines).strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an invalid response. Please try again.",
        ) from e

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an unexpected response format.",
        )

    return parsed


def validate_gemini_response(raw_data: dict) -> ResumeAnalysis:
    try:
        return ResumeAnalysis(**raw_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini's response didn't match the expected format.",
        ) from e