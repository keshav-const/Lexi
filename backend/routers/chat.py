"""
Chat Router - Template matching, Q&A flow, and draft generation.
CREATED BY UOIONHHC
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db, Instance
from models import (
    ChatMatchRequest, ChatMatchResponse, TemplateMatchResult,
    ChatQuestionsRequest, ChatQuestionsResponse, VariableQuestion,
    DraftGenerateRequest, DraftGenerateResponse
)
from services.template_service import get_template, find_best_match, render_draft
from services.gemini_service import generate_questions, prefill_variables

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/match", response_model=ChatMatchResponse)
async def match_template_for_query(
    request: ChatMatchRequest,
    db: Session = Depends(get_db)
):
    """
    Find the best matching template for a user query.
    
    - Searches templates using Gemini classification + embeddings
    - Returns best match with score and reason
    - Also returns alternatives and prefilled variables
    """
    try:
        # Find matching templates
        match_result = await find_best_match(db, request.query)
        
        if not match_result.get("best_match"):
            return ChatMatchResponse(
                best_match=None,
                alternatives=[],
                prefilled_variables={},
                missing_variables=[]
            )
        
        # Get the best matching template
        best_match = match_result["best_match"]
        template = get_template(db, best_match["template_id"])
        
        if not template:
            return ChatMatchResponse(
                best_match=None,
                alternatives=match_result.get("alternatives", []),
                prefilled_variables={},
                missing_variables=[]
            )
        
        # Try to prefill variables from the query
        variables_for_prefill = [
            {
                "key": v.key,
                "label": v.label,
                "description": v.description,
                "dtype": v.dtype
            }
            for v in template.variables
        ]
        
        prefill_result = await prefill_variables(request.query, variables_for_prefill)
        prefilled = prefill_result.get("prefilled", {})
        
        # Find missing variables
        all_keys = {v.key for v in template.variables}
        filled_keys = set(prefilled.keys())
        missing = list(all_keys - filled_keys)
        
        # Convert best match to response format
        best_match_response = TemplateMatchResult(
            template_id=best_match["template_id"],
            title=best_match["title"],
            score=best_match["score"],
            reason=best_match["reason"],
            doc_type=best_match.get("doc_type"),
            similarity_tags=best_match.get("similarity_tags", [])
        )
        
        # Convert alternatives
        alternatives = [
            TemplateMatchResult(
                template_id=alt["template_id"],
                title=alt["title"],
                score=alt["score"],
                reason=alt["reason"],
                doc_type=alt.get("doc_type"),
                similarity_tags=alt.get("similarity_tags", [])
            )
            for alt in match_result.get("alternatives", [])
        ]
        
        return ChatMatchResponse(
            best_match=best_match_response,
            alternatives=alternatives,
            prefilled_variables=prefilled,
            missing_variables=missing
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching template: {str(e)}")


@router.post("/questions", response_model=ChatQuestionsResponse)
async def get_questions_for_variables(
    request: ChatQuestionsRequest,
    db: Session = Depends(get_db)
):
    """
    Generate human-friendly questions for missing variables.
    
    - Converts variable definitions to polite questions
    - Includes hints and examples
    """
    try:
        template = get_template(db, request.template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Get variables that need questions
        missing_vars = [
            {
                "key": v.key,
                "label": v.label,
                "description": v.description,
                "example": v.example,
                "required": v.required,
                "dtype": v.dtype
            }
            for v in template.variables
            if v.key in request.missing_keys
        ]
        
        if not missing_vars:
            return ChatQuestionsResponse(questions=[])
        
        # Generate questions using Gemini
        questions_list = await generate_questions(missing_vars)
        
        # Convert to response format
        questions = [
            VariableQuestion(
                key=q["key"],
                question=q["question"],
                hint=q.get("hint"),
                example=q.get("example"),
                required=q.get("required", True)
            )
            for q in questions_list
        ]
        
        return ChatQuestionsResponse(questions=questions)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


@router.post("/generate", response_model=DraftGenerateResponse)
async def generate_draft(
    request: DraftGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a draft document from template and answers.
    
    - Substitutes all variables in template
    - Saves draft instance to database
    - Returns rendered Markdown
    """
    try:
        template = get_template(db, request.template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Render the draft
        draft_md = render_draft(template, request.answers)
        
        # Save instance to database
        instance = Instance(
            template_id=template.id,
            user_query=request.user_query,
            answers_json=request.answers,
            draft_md=draft_md
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)
        
        return DraftGenerateResponse(
            draft_id=instance.id,
            draft_md=draft_md,
            template_title=template.title,
            created_at=instance.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating draft: {str(e)}")


@router.get("/vars/{template_id}")
async def get_template_variables_status(
    template_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the list of all variables for a template (for /vars command).
    """
    template = get_template(db, template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {
        "template_id": template_id,
        "template_title": template.title,
        "variables": [
            {
                "key": v.key,
                "label": v.label,
                "required": v.required,
                "dtype": v.dtype,
                "example": v.example
            }
            for v in template.variables
        ]
    }
