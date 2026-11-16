import logging

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.schemas.resume import ResumeUploadResponse
from app.services.pdf_service import validate_and_read_pdf, extract_text_from_pdf
from app.services.gemini_service import analyze_resume_text, validate_gemini_response
from app.utils.normalization import normalize_skills
from app.services.resume_service import save_resume_analysis
from app.services.auth_service import reserve_ai_request
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/resume", tags=["resume"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        file_bytes = await validate_and_read_pdf(file)
        extracted_text = await run_in_threadpool(
            extract_text_from_pdf,
            file_bytes,
        )

        reserve_ai_request(current_user["email"])
        raw_analysis = await run_in_threadpool(
            analyze_resume_text,
            extracted_text,
        )
        raw_analysis["skills"] = normalize_skills(
            raw_analysis.get("skills", [])
        )

        validated_analysis = validate_gemini_response(raw_analysis)

        try:
            await run_in_threadpool(
                save_resume_analysis,
                current_user["email"],
                validated_analysis,
            )
        except Exception as exc:
            logger.exception("Failed to save analyzed resume")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal server error occurred while saving your resume data."
            ) from exc

        return {
            "message": "Resume uploaded and analyzed successfully.",
            "filename": file.filename,
            "size_kb": round(len(file_bytes) / 1024, 2),
            "analysis": validated_analysis
        }
    finally:
        await file.close()