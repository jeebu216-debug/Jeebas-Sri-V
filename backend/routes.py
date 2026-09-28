from base64 import b64encode

from fastapi import APIRouter, HTTPException

from backend.ai_core.gemini_generator import GeminiDocumentGenerator
from backend.models import (
    DocumentRequest,
    ExportRequest,
    GenerateResponse,
)
from backend.services.document_export import make_export


router = APIRouter()


# =========================================================
# GENERATE DOCUMENT
# =========================================================

@router.post(
    "/generate",
    response_model=GenerateResponse,
)
def generate_document(
    payload: DocumentRequest,
):
    try:
        generator = GeminiDocumentGenerator()

        text = generator.generate_document(
            document_type=payload.document_type,
            parties=payload.parties,
            terms=payload.terms,
            effective_date=payload.effective_date,
        )

        return GenerateResponse(
            success=True,
            document_type=payload.document_type,
            text=text,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc


# =========================================================
# EXPORT DOCUMENT
# =========================================================

@router.post("/export")
def export_document(
    payload: ExportRequest,
):
    try:
        # Use the already-generated document text.
        text = payload.text or ""

        # Get the requested format.
        file_format = payload.format.lower().strip()

        # Create the actual file.
        data = make_export(
            text=text,
            doc_type=payload.document_type,
            file_format=file_format,
            terms=payload.terms or "",
        )

        # File information.
        if file_format == "pdf":
            extension = "pdf"
            media_type = "application/pdf"

        elif file_format == "docx":
            extension = "docx"
            media_type = (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            )

        elif file_format == "txt":
            extension = "txt"
            media_type = "text/plain"

        else:
            raise ValueError(
                f"Unsupported export format: {payload.format}"
            )

        filename = f"LegalEase_Document.{extension}"

        # Convert file bytes to Base64 so the frontend can download them.
        data_base64 = b64encode(data).decode("utf-8")

        return {
            "success": True,
            "filename": filename,
            "media_type": media_type,
            "data_base64": data_base64,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc