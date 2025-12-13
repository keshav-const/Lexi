"""
Templates Router - CRUD operations for templates.
CREATED BY UOIONHHC
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, Template
from models import (
    TemplateCreate, TemplateResponse, TemplateListResponse,
    VariableResponse
)
from services.template_service import (
    create_template, get_template, list_templates, delete_template,
    export_variables, generate_yaml_frontmatter
)
from services.gemini_service import generate_embedding, generate_template_body

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.post("", response_model=TemplateResponse)
async def create_new_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Save a new template to the database.
    
    - Creates template with YAML front-matter format
    - Stores all variables
    - Generates embedding for similarity search
    """
    try:
        # Generate embedding for the template
        embedding_text = f"{template_data.title} {template_data.file_description or ''} {' '.join(template_data.similarity_tags)}"
        embedding = await generate_embedding(embedding_text)
        
        # Create template
        template = create_template(
            db=db,
            title=template_data.title,
            body_md=template_data.body_md,
            variables=[v.model_dump() for v in template_data.variables],
            doc_type=template_data.doc_type,
            jurisdiction=template_data.jurisdiction,
            file_description=template_data.file_description,
            similarity_tags=template_data.similarity_tags,
            embedding=embedding
        )
        
        return template
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")


@router.get("", response_model=list[TemplateListResponse])
async def get_all_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    List all templates with pagination.
    """
    templates = list_templates(db, skip=skip, limit=limit)
    
    return [
        TemplateListResponse(
            id=t.id,
            template_id=t.template_id,
            title=t.title,
            doc_type=t.doc_type,
            jurisdiction=t.jurisdiction,
            similarity_tags=t.similarity_tags or [],
            variable_count=len(t.variables),
            created_at=t.created_at
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_single_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a single template by its template_id.
    """
    template = get_template(db, template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.delete("/{template_id}")
async def delete_single_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a template by its template_id.
    """
    success = delete_template(db, template_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"message": "Template deleted successfully", "template_id": template_id}


@router.get("/{template_id}/export")
async def export_template_variables(
    template_id: str,
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """
    Export template variables in JSON or CSV format.
    """
    template = get_template(db, template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    content = export_variables(template, format)
    
    if format == "csv":
        return PlainTextResponse(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={template_id}_variables.csv"}
        )
    
    return {"template_id": template_id, "variables": content}


@router.get("/{template_id}/markdown", response_class=PlainTextResponse)
async def get_template_markdown(
    template_id: str,
    include_frontmatter: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Get the full template as Markdown with optional YAML front-matter.
    """
    template = get_template(db, template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if include_frontmatter:
        content = generate_yaml_frontmatter(template) + template.body_md
    else:
        content = template.body_md
    
    return PlainTextResponse(
        content=content,
        headers={"Content-Disposition": f"attachment; filename={template_id}.md"}
    )
