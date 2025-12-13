from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============ Variable Schemas ============

class VariableBase(BaseModel):
    """Base schema for template variables."""
    key: str = Field(..., description="snake_case variable key")
    label: str = Field(..., description="Human-readable label")
    description: Optional[str] = Field(None, description="What this field represents")
    example: Optional[str] = Field(None, description="Example value")
    required: bool = Field(True, description="Whether this variable is required")
    dtype: str = Field("string", description="Data type: string, date, number, currency")
    regex: Optional[str] = Field(None, description="Validation regex pattern")
    enum_values: Optional[list[str]] = Field(None, description="Allowed values for enum type")


class VariableCreate(VariableBase):
    """Schema for creating a variable."""
    pass


class VariableResponse(VariableBase):
    """Schema for variable response."""
    id: int
    
    class Config:
        from_attributes = True


class VariableQuestion(BaseModel):
    """Schema for human-friendly question."""
    key: str
    question: str
    hint: Optional[str] = None
    example: Optional[str] = None
    required: bool = True


# ============ Template Schemas ============

class TemplateBase(BaseModel):
    """Base schema for templates."""
    title: str
    doc_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    file_description: Optional[str] = None
    similarity_tags: list[str] = Field(default_factory=list)


class TemplateCreate(TemplateBase):
    """Schema for creating a template."""
    body_md: str
    variables: list[VariableCreate] = Field(default_factory=list)


class TemplateResponse(TemplateBase):
    """Schema for template response."""
    id: int
    template_id: str
    body_md: str
    variables: list[VariableResponse] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Schema for listing templates."""
    id: int
    template_id: str
    title: str
    doc_type: Optional[str]
    jurisdiction: Optional[str]
    similarity_tags: list[str]
    variable_count: int
    created_at: datetime


class TemplateMatchResult(BaseModel):
    """Schema for template matching result."""
    template_id: str
    title: str
    score: float = Field(..., ge=0, le=1, description="Match confidence score")
    reason: str
    doc_type: Optional[str]
    similarity_tags: list[str]


# ============ Document Schemas ============

class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""
    filename: str
    extracted_text_preview: str
    variables: list[VariableBase]
    suggested_title: str
    suggested_doc_type: str
    similarity_tags: list[str]


class DocumentParseResult(BaseModel):
    """Result of parsing a document."""
    text: str
    filename: str
    mime_type: str


# ============ Chat Schemas ============

class ChatMatchRequest(BaseModel):
    """Request to find matching template."""
    query: str = Field(..., description="User's draft request")


class ChatMatchResponse(BaseModel):
    """Response with matching templates."""
    best_match: Optional[TemplateMatchResult] = None
    alternatives: list[TemplateMatchResult] = []
    prefilled_variables: dict[str, str] = {}
    missing_variables: list[str] = []


class ChatQuestionsRequest(BaseModel):
    """Request to generate questions for missing variables."""
    template_id: str
    missing_keys: list[str]


class ChatQuestionsResponse(BaseModel):
    """Response with human-friendly questions."""
    questions: list[VariableQuestion]


# ============ Draft Schemas ============

class DraftGenerateRequest(BaseModel):
    """Request to generate a draft."""
    template_id: str
    answers: dict[str, str] = Field(..., description="Variable key-value pairs")
    user_query: Optional[str] = None


class DraftGenerateResponse(BaseModel):
    """Response with generated draft."""
    draft_id: int
    draft_md: str
    template_title: str
    created_at: datetime


# ============ Exa.ai Schemas (Bonus) ============

class ExaSearchRequest(BaseModel):
    """Request to search for templates via Exa.ai."""
    query: str
    num_results: int = Field(3, ge=1, le=10)


class ExaSearchResult(BaseModel):
    """Single search result from Exa.ai."""
    title: str
    url: str
    snippet: str
    score: float


class ExaSearchResponse(BaseModel):
    """Response from Exa.ai search."""
    results: list[ExaSearchResult]
    query: str
