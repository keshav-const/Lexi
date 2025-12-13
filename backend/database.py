from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

DATABASE_URL = "sqlite:///./data/lexi.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite specific
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Template(Base):
    """Template model for storing document templates."""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(100), unique=True, index=True)  # e.g., tpl_incident_notice_v1
    title = Column(String(255), nullable=False)
    doc_type = Column(String(100))  # legal_notice, contract, agreement, letter
    jurisdiction = Column(String(50))  # IN, US, UK, etc.
    file_description = Column(Text)  # Description for case matching
    similarity_tags = Column(JSON)  # ["insurance", "notice", "india"]
    body_md = Column(Text, nullable=False)  # Markdown template with {{variables}}
    embedding = Column(JSON)  # Vector embedding for similarity search
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to variables
    variables = relationship("TemplateVariable", back_populates="template", cascade="all, delete-orphan")
    instances = relationship("Instance", back_populates="template")


class TemplateVariable(Base):
    """Template variable model."""
    __tablename__ = "template_variables"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    key = Column(String(100), nullable=False)  # snake_case key
    label = Column(String(255), nullable=False)  # Human-readable label
    description = Column(Text)  # What this field represents
    example = Column(String(500))  # Example value
    required = Column(Boolean, default=True)
    dtype = Column(String(50), default="string")  # string, date, number, currency
    regex = Column(String(255))  # Optional validation regex
    enum_values = Column(JSON)  # Optional enum values
    
    # Relationship
    template = relationship("Template", back_populates="variables")


class Document(Base):
    """Uploaded document model."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    mime = Column(String(100))
    raw_text = Column(Text)  # Extracted text content
    embedding = Column(JSON)  # Vector embedding
    created_at = Column(DateTime, default=datetime.utcnow)


class Instance(Base):
    """Draft instance model - a generated document from a template."""
    __tablename__ = "instances"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    user_query = Column(Text)  # Original user request
    answers_json = Column(JSON)  # Filled variable values
    draft_md = Column(Text)  # Generated Markdown draft
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    template = relationship("Template", back_populates="instances")


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
