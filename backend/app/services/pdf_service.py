from fastapi import HTTPException, status, UploadFile
import pymupdf as fitz

MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_PDF_PAGES = 20
MAX_EXTRACTED_TEXT_CHARACTERS = 50_000
ALLOWED_CONTENT_TYPE = "application/pdf"


async def validate_and_read_pdf(file: UploadFile) -> bytes:
    if file.content_type != ALLOWED_CONTENT_TYPE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed."
        )

    if file.size is not None and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum allowed is {MAX_FILE_SIZE_MB}MB."
        )

    # Read at most 1 byte over the limit to avoid loading a huge upload.
    file_bytes = await file.read(MAX_FILE_SIZE_BYTES + 1)

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB."
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    return file_bytes


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            if doc.is_encrypted or doc.needs_pass:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This PDF is password-protected. Please upload an unencrypted PDF."
                )

            if doc.page_count > MAX_PDF_PAGES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PDF has too many pages. Maximum allowed is {MAX_PDF_PAGES}."
                )

            pages_text = []
            extracted_characters = 0
            for page in doc:
                page_text = page.get_text()
                extracted_characters += len(page_text) + (
                    1 if pages_text else 0
                )
                if extracted_characters > MAX_EXTRACTED_TEXT_CHARACTERS:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            "Extracted text is too long. Maximum allowed is "
                            f"{MAX_EXTRACTED_TEXT_CHARACTERS} characters."
                        )
                    )
                pages_text.append(page_text)

            text = "\n".join(pages_text)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not open file. Please upload a valid PDF."
        )

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No readable text found in this PDF. It may be a scanned image."
        )

    return text
