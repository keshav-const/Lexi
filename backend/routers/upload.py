"""
Upload Router - Handle document uploads and variable extraction.
CREATED BY UOIONHHC
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db, Document
from models import DocumentUploadResponse, VariableBase
from services.document_parser import parse_document, get_text_preview
from services.gemini_service import extract_variables, generate_embedding
from config import get_settings

router = APIRouter(prefix="/api/upload", tags=["upload"])
settings = get_settings()


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document and extract variables for templatization.
    
    - Accepts .docx and .pdf files
    - Extracts text content
    - Uses Gemini to identify variables
    - Returns preview for user review
    """
    # Validate file extension
    filename = file.filename or "unknown"
    extension = "." + filename.split(".")[-1].lower() if "." in filename else ""
    
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    try:
        # Parse document
        text, mime = await parse_document(content, filename)
        
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract any text from the document"
            )
        
        # Store document record
        doc = Document(
            filename=filename,
            mime=mime,
            raw_text=text
        )
        db.add(doc)
        db.commit()
        
        # Extract variables using Gemini
        extraction_result = await extract_variables(text)
        
        # Convert variables to response format
        variables = [
            VariableBase(
                key=v["key"],
                label=v["label"],
                description=v.get("description"),
                example=v.get("example"),
                required=v.get("required", True),
                dtype=v.get("dtype", "string")
            )
            for v in extraction_result.get("variables", [])
        ]
        
        return DocumentUploadResponse(
            filename=filename,
            extracted_text_preview=get_text_preview(text, 500),
            variables=variables,
            suggested_title=extraction_result.get("title", filename.rsplit(".", 1)[0]),
            suggested_doc_type=extraction_result.get("doc_type", "other"),
            similarity_tags=extraction_result.get("similarity_tags", [])
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
