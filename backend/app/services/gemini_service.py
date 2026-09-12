import os
import json
from google import genai
from dotenv import load_dotenv
from fastapi import HTTPException, status

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

If a section has no information, return an empty list for it. Do not invent information that isn't in the resume text.

Resume text:
"""


def analyze_resume_text(resume_text: str) -> dict:
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=EXTRACTION_PROMPT + resume_text
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to reach Gemini API: {str(e)}"
        )

    raw_text = response.text.strip()

    # Gemini sometimes wraps JSON in markdown code fences - strip those if present
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an invalid response. Please try again."
        )

    return parsed

from pydantic import ValidationError
from app.schemas.resume import ResumeAnalysis


def validate_gemini_response(raw_data: dict) -> ResumeAnalysis:
    try:
        return ResumeAnalysis(**raw_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini's response didn't match the expected format: {str(e)}"
        )