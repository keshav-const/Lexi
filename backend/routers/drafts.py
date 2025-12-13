"""
Drafts Router - Draft history and management.
CREATED BY UOIONHHC
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from database import get_db, Instance

router = APIRouter(prefix="/api/drafts", tags=["drafts"])


@router.get("")
async def list_drafts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all draft instances with pagination.
    """
    instances = db.query(Instance).order_by(Instance.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": i.id,
            "template_id": i.template.template_id if i.template else None,
            "template_title": i.template.title if i.template else "Unknown",
            "user_query": i.user_query,
            "preview": i.draft_md[:200] + "..." if len(i.draft_md) > 200 else i.draft_md,
            "created_at": i.created_at
        }
        for i in instances
    ]


@router.get("/{draft_id}")
async def get_draft(
    draft_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single draft by ID.
    """
    instance = db.query(Instance).filter(Instance.id == draft_id).first()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return {
        "id": instance.id,
        "template_id": instance.template.template_id if instance.template else None,
        "template_title": instance.template.title if instance.template else "Unknown",
        "user_query": instance.user_query,
        "answers": instance.answers_json,
        "draft_md": instance.draft_md,
        "created_at": instance.created_at
    }


@router.get("/{draft_id}/download", response_class=PlainTextResponse)
async def download_draft(
    draft_id: int,
    db: Session = Depends(get_db)
):
    """
    Download a draft as a Markdown file.
    """
    instance = db.query(Instance).filter(Instance.id == draft_id).first()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    template_title = instance.template.title if instance.template else "draft"
    filename = f"{template_title.lower().replace(' ', '_')}_{draft_id}.md"
    
    return PlainTextResponse(
        content=instance.draft_md,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a draft by ID.
    """
    instance = db.query(Instance).filter(Instance.id == draft_id).first()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    db.delete(instance)
    db.commit()
    
    return {"message": "Draft deleted successfully", "draft_id": draft_id}
