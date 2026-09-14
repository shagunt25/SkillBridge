from fastapi import APIRouter, UploadFile, File, Depends
from app.schemas.resume import ResumeUploadResponse
from app.services.pdf_service import validate_and_read_pdf, extract_text_from_pdf
from app.services.gemini_service import analyze_resume_text, validate_gemini_response
from app.utils.normalization import normalize_skills
from app.services.resume_service import save_resume_analysis
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    file_bytes = await validate_and_read_pdf(file)
    extracted_text = extract_text_from_pdf(file_bytes)

    raw_analysis = analyze_resume_text(extracted_text)
    validated_analysis = validate_gemini_response(raw_analysis)

    validated_analysis.skills = normalize_skills(
        [skill.model_dump() for skill in validated_analysis.skills]
    )

    save_resume_analysis(current_user["email"], validated_analysis)

    return {
        "message": "Resume uploaded and analyzed successfully.",
        "filename": file.filename,
        "size_kb": round(len(file_bytes) / 1024, 2),
        "analysis": validated_analysis
    }