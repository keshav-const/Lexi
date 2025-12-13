"""
Template Service for CRUD operations and matching.
CREATED BY UOIONHHC
"""
import json
import re
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from database import Template, TemplateVariable
from services.gemini_service import generate_embedding, cosine_similarity, match_template


def generate_template_id(title: str) -> str:
    """Generate a unique template ID from title."""
    # Convert title to snake_case
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
    slug = re.sub(r'\s+', '_', slug)
    # Add version
    short_id = str(uuid.uuid4())[:8]
    return f"tpl_{slug[:30]}_{short_id}"


def create_template(
    db: Session,
    title: str,
    body_md: str,
    variables: list[dict],
    doc_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    file_description: Optional[str] = None,
    similarity_tags: Optional[list[str]] = None,
    embedding: Optional[list[float]] = None
) -> Template:
    """
    Create a new template in the database.
    
    Args:
        db: Database session
        title: Template title
        body_md: Markdown template body with {{variables}}
        variables: List of variable dicts
        doc_type: Document type (legal_notice, contract, etc.)
        jurisdiction: Jurisdiction code (IN, US, etc.)
        file_description: Description for matching
        similarity_tags: Tags for similarity search
        embedding: Vector embedding
    
    Returns:
        Created Template object
    """
    template_id = generate_template_id(title)
    
    # Create template
    template = Template(
        template_id=template_id,
        title=title,
        doc_type=doc_type,
        jurisdiction=jurisdiction,
        file_description=file_description,
        similarity_tags=similarity_tags or [],
        body_md=body_md,
        embedding=embedding
    )
    
    db.add(template)
    db.flush()  # Get the template ID
    
    # Create variables
    for var in variables:
        variable = TemplateVariable(
            template_id=template.id,
            key=var["key"],
            label=var["label"],
            description=var.get("description"),
            example=var.get("example"),
            required=var.get("required", True),
            dtype=var.get("dtype", "string"),
            regex=var.get("regex"),
            enum_values=var.get("enum_values")
        )
        db.add(variable)
    
    db.commit()
    db.refresh(template)
    
    return template


def get_template(db: Session, template_id: str) -> Optional[Template]:
    """Get a template by its template_id."""
    return db.query(Template).filter(Template.template_id == template_id).first()


def get_template_by_id(db: Session, id: int) -> Optional[Template]:
    """Get a template by its database ID."""
    return db.query(Template).filter(Template.id == id).first()


def list_templates(db: Session, skip: int = 0, limit: int = 100) -> list[Template]:
    """List all templates with pagination."""
    return db.query(Template).offset(skip).limit(limit).all()


def delete_template(db: Session, template_id: str) -> bool:
    """Delete a template by its template_id."""
    template = get_template(db, template_id)
    if template:
        db.delete(template)
        db.commit()
        return True
    return False


async def find_best_match(db: Session, user_query: str) -> dict:
    """
    Find the best matching template for a user query.
    Uses both Gemini classification and embedding similarity.
    
    Args:
        db: Database session
        user_query: User's document request
    
    Returns:
        dict with best_match, alternatives, and no_match_reason if none found
    """
    templates = list_templates(db)
    if not templates:
        return {
            "best_match": None,
            "alternatives": [],
            "no_match_reason": "No templates available in database"
        }
    
    # Prepare templates for matching
    templates_for_matching = [
        {
            "template_id": t.template_id,
            "title": t.title,
            "doc_type": t.doc_type,
            "file_description": t.file_description,
            "similarity_tags": t.similarity_tags or []
        }
        for t in templates
    ]
    
    # Use Gemini for intelligent matching
    match_result = await match_template(user_query, templates_for_matching)
    
    if not match_result.get("matches"):
        return {
            "best_match": None,
            "alternatives": [],
            "no_match_reason": match_result.get("no_match_reason", "No matching templates found")
        }
    
    # Get full template details for matches
    matches = []
    for m in match_result["matches"]:
        template = get_template(db, m["template_id"])
        if template:
            matches.append({
                "template_id": template.template_id,
                "title": template.title,
                "score": m["score"],
                "reason": m["reason"],
                "doc_type": template.doc_type,
                "similarity_tags": template.similarity_tags or []
            })
    
    if not matches:
        return {
            "best_match": None,
            "alternatives": [],
            "no_match_reason": "Matched templates not found in database"
        }
    
    return {
        "best_match": matches[0] if matches else None,
        "alternatives": matches[1:3] if len(matches) > 1 else []
    }


def render_draft(template: Template, answers: dict[str, str]) -> str:
    """
    Render a draft by substituting variables in the template.
    
    Args:
        template: Template object
        answers: Dictionary of variable key -> value
    
    Returns:
        Rendered Markdown string
    """
    draft = template.body_md
    
    # Get all variable keys from template
    var_keys = {v.key for v in template.variables}
    
    # Substitute variables
    for key, value in answers.items():
        placeholder = "{{" + key + "}}"
        draft = draft.replace(placeholder, str(value))
    
    # Check for any remaining unsubstituted variables
    remaining = re.findall(r'\{\{(\w+)\}\}', draft)
    if remaining:
        # Mark missing variables
        for var in remaining:
            draft = draft.replace("{{" + var + "}}", f"[MISSING: {var}]")
    
    return draft


def export_variables(template: Template, format: str = "json") -> str:
    """
    Export template variables to JSON or CSV format.
    
    Args:
        template: Template object
        format: "json" or "csv"
    
    Returns:
        Formatted string
    """
    variables = [
        {
            "key": v.key,
            "label": v.label,
            "description": v.description,
            "example": v.example,
            "required": v.required,
            "dtype": v.dtype
        }
        for v in template.variables
    ]
    
    if format == "json":
        return json.dumps(variables, indent=2)
    elif format == "csv":
        if not variables:
            return "key,label,description,example,required,dtype"
        
        lines = ["key,label,description,example,required,dtype"]
        for v in variables:
            line = f'"{v["key"]}","{v["label"]}","{v.get("description", "")}","{v.get("example", "")}",{v["required"]},"{v["dtype"]}"'
            lines.append(line)
        return "\n".join(lines)
    else:
        raise ValueError(f"Unsupported format: {format}")


def generate_yaml_frontmatter(template: Template) -> str:
    """Generate YAML front-matter for a template."""
    variables_yaml = []
    for v in template.variables:
        var_yaml = f"""  - key: {v.key}
    label: {v.label}
    description: {v.description or ''}
    example: "{v.example or ''}"
    required: {str(v.required).lower()}"""
        variables_yaml.append(var_yaml)
    
    frontmatter = f"""---
template_id: {template.template_id}
title: {template.title}
file_description: {template.file_description or ''}
jurisdiction: {template.jurisdiction or ''}
doc_type: {template.doc_type or ''}
variables:
{chr(10).join(variables_yaml)}
similarity_tags: {json.dumps(template.similarity_tags or [])}
---

"""
    return frontmatter
