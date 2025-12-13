"""
Lexi - Document Templatization System
Main FastAPI Application Entry Point
CREATED BY UOIONHHC
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db
from routers import upload, templates, chat, drafts
from config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("🚀 Starting Lexi - Document Templatization System")
    init_db()
    
    # Seed sample templates if database is empty
    await seed_sample_templates()
    
    yield
    
    # Shutdown
    print("👋 Shutting down Lexi")


app = FastAPI(
    title="Lexi - Document Templatization",
    description="Upload legal documents, convert to templates, and generate drafts with AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(templates.router)
app.include_router(chat.router)
app.include_router(drafts.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": "Lexi - Document Templatization System",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """API health check."""
    return {"status": "healthy"}


async def seed_sample_templates():
    """Seed sample templates if database is empty."""
    from database import SessionLocal, Template
    from services.template_service import create_template
    from services.gemini_service import generate_embedding
    
    db = SessionLocal()
    
    try:
        # Check if templates exist
        existing = db.query(Template).count()
        if existing > 0:
            print(f"📋 Found {existing} existing templates")
            return
        
        print("🌱 Seeding sample templates...")
        
        # Sample templates
        sample_templates = get_sample_templates()
        
        for template_data in sample_templates:
            try:
                # Generate embedding
                embedding_text = f"{template_data['title']} {template_data.get('file_description', '')} {' '.join(template_data.get('similarity_tags', []))}"
                embedding = await generate_embedding(embedding_text)
                
                create_template(
                    db=db,
                    title=template_data["title"],
                    body_md=template_data["body_md"],
                    variables=template_data["variables"],
                    doc_type=template_data.get("doc_type"),
                    jurisdiction=template_data.get("jurisdiction"),
                    file_description=template_data.get("file_description"),
                    similarity_tags=template_data.get("similarity_tags", []),
                    embedding=embedding
                )
                print(f"  ✅ Created: {template_data['title']}")
            except Exception as e:
                print(f"  ❌ Failed to create {template_data['title']}: {e}")
        
        print("🌱 Sample templates seeded successfully!")
        
    finally:
        db.close()


def get_sample_templates() -> list[dict]:
    """Get the 5 sample templates for seeding."""
    return [
        # 1. Legal Notice to Insurer (India)
        {
            "title": "Incident Notice to Insurer",
            "doc_type": "legal_notice",
            "jurisdiction": "IN",
            "file_description": "A formal notice sent to an insurance company to report an incident and initiate a claim under a policy.",
            "similarity_tags": ["insurance", "notice", "claim", "india", "motor", "health", "accident"],
            "variables": [
                {"key": "claimant_full_name", "label": "Claimant's Full Name", "description": "Person or entity raising the insurance claim", "example": "Rahul Kumar", "required": True, "dtype": "string"},
                {"key": "claimant_address", "label": "Claimant's Address", "description": "Complete postal address of the claimant", "example": "123 MG Road, Mumbai 400001", "required": True, "dtype": "address"},
                {"key": "insurer_name", "label": "Insurance Company Name", "description": "Name of the insurance company", "example": "ICICI Lombard General Insurance", "required": True, "dtype": "string"},
                {"key": "policy_number", "label": "Policy Number", "description": "Insurance policy reference number as printed on schedule", "example": "POL-2024-12345678", "required": True, "dtype": "string"},
                {"key": "incident_date", "label": "Date of Incident", "description": "The date when the insured event occurred", "example": "2024-12-01", "required": True, "dtype": "date"},
                {"key": "incident_description", "label": "Incident Description", "description": "Brief description of what happened", "example": "Vehicle collision at intersection", "required": True, "dtype": "string"},
                {"key": "claim_amount", "label": "Claim Amount (INR)", "description": "Total amount being claimed", "example": "150000", "required": False, "dtype": "currency"},
                {"key": "notice_date", "label": "Notice Date", "description": "Date of this notice", "example": "2024-12-10", "required": True, "dtype": "date"}
            ],
            "body_md": """# NOTICE OF INCIDENT TO INSURER

**Date:** {{notice_date}}

**To:**  
{{insurer_name}}  
Claims Department

**From:**  
{{claimant_full_name}}  
{{claimant_address}}

**Re: Notice of Incident Under Policy No. {{policy_number}}**

---

Dear Sir/Madam,

I, **{{claimant_full_name}}**, hereby notify you of an incident that occurred on **{{incident_date}}** that may give rise to a claim under the above-referenced insurance policy.

## Incident Details

**Date of Incident:** {{incident_date}}

**Description:** {{incident_description}}

## Claim Information

I am filing this notice to preserve my rights under the policy and to initiate the claims process. The estimated claim amount is **INR {{claim_amount}}** (subject to assessment).

## Required Actions

Please acknowledge receipt of this notice and provide me with:
1. Claim reference number
2. List of required documents
3. Surveyor appointment details (if applicable)

I am available for any inspection or further information you may require.

Yours faithfully,

**{{claimant_full_name}}**

---
*This notice is sent in compliance with the terms of Policy No. {{policy_number}}*
"""
        },
        
        # 2. Non-Disclosure Agreement (NDA)
        {
            "title": "Non-Disclosure Agreement (NDA)",
            "doc_type": "agreement",
            "jurisdiction": "US",
            "file_description": "A mutual or one-way non-disclosure agreement to protect confidential information between parties.",
            "similarity_tags": ["nda", "confidentiality", "agreement", "contract", "business", "legal"],
            "variables": [
                {"key": "disclosing_party_name", "label": "Disclosing Party Name", "description": "The party sharing confidential information", "example": "TechCorp Inc.", "required": True, "dtype": "string"},
                {"key": "receiving_party_name", "label": "Receiving Party Name", "description": "The party receiving confidential information", "example": "John Smith", "required": True, "dtype": "string"},
                {"key": "effective_date", "label": "Effective Date", "description": "Date when the agreement becomes effective", "example": "2024-12-01", "required": True, "dtype": "date"},
                {"key": "confidentiality_period", "label": "Confidentiality Period", "description": "Duration of confidentiality obligation in years", "example": "3", "required": True, "dtype": "number"},
                {"key": "purpose", "label": "Purpose of Disclosure", "description": "The business purpose for sharing information", "example": "Evaluating potential business partnership", "required": True, "dtype": "string"},
                {"key": "governing_law", "label": "Governing Law State", "description": "State whose laws govern the agreement", "example": "Delaware", "required": True, "dtype": "string"}
            ],
            "body_md": """# NON-DISCLOSURE AGREEMENT

**Effective Date:** {{effective_date}}

---

This Non-Disclosure Agreement ("Agreement") is entered into by and between:

**Disclosing Party:** {{disclosing_party_name}}

**Receiving Party:** {{receiving_party_name}}

## 1. PURPOSE

The Disclosing Party wishes to disclose certain confidential information to the Receiving Party for the purpose of: **{{purpose}}**.

## 2. DEFINITION OF CONFIDENTIAL INFORMATION

"Confidential Information" means any non-public information disclosed by the Disclosing Party, including but not limited to:
- Trade secrets and proprietary data
- Business plans and strategies
- Technical specifications and designs
- Customer and supplier information
- Financial information

## 3. OBLIGATIONS OF RECEIVING PARTY

The Receiving Party agrees to:
1. Keep all Confidential Information strictly confidential
2. Use Confidential Information only for the stated Purpose
3. Not disclose to third parties without prior written consent
4. Use reasonable security measures to protect the information

## 4. TERM

The confidentiality obligations shall remain in effect for **{{confidentiality_period}} years** from the Effective Date.

## 5. GOVERNING LAW

This Agreement shall be governed by the laws of the State of **{{governing_law}}**.

---

**AGREED AND ACCEPTED:**

**Disclosing Party:**  
{{disclosing_party_name}}  
Date: _____________

**Receiving Party:**  
{{receiving_party_name}}  
Date: _____________
"""
        },
        
        # 3. Employment Offer Letter
        {
            "title": "Employment Offer Letter",
            "doc_type": "letter",
            "jurisdiction": "US",
            "file_description": "A formal job offer letter extending employment to a candidate with terms and conditions.",
            "similarity_tags": ["employment", "offer", "job", "letter", "hr", "hiring", "salary"],
            "variables": [
                {"key": "candidate_name", "label": "Candidate Name", "description": "Full name of the job candidate", "example": "Sarah Johnson", "required": True, "dtype": "string"},
                {"key": "company_name", "label": "Company Name", "description": "Name of the hiring company", "example": "Acme Technologies", "required": True, "dtype": "string"},
                {"key": "position_title", "label": "Position Title", "description": "Job title being offered", "example": "Senior Software Engineer", "required": True, "dtype": "string"},
                {"key": "department", "label": "Department", "description": "Department the position is in", "example": "Engineering", "required": True, "dtype": "string"},
                {"key": "start_date", "label": "Start Date", "description": "Proposed employment start date", "example": "2025-01-15", "required": True, "dtype": "date"},
                {"key": "salary", "label": "Annual Salary", "description": "Annual base salary in USD", "example": "120000", "required": True, "dtype": "currency"},
                {"key": "manager_name", "label": "Reporting Manager", "description": "Name of the direct supervisor", "example": "Michael Chen", "required": True, "dtype": "string"},
                {"key": "hr_contact", "label": "HR Contact", "description": "HR representative name", "example": "Lisa Wong", "required": True, "dtype": "string"},
                {"key": "offer_expiry_date", "label": "Offer Expiry Date", "description": "Date by which offer must be accepted", "example": "2024-12-20", "required": True, "dtype": "date"}
            ],
            "body_md": """# EMPLOYMENT OFFER LETTER

**{{company_name}}**

---

**Date:** {{offer_expiry_date}}

**To:** {{candidate_name}}

Dear {{candidate_name}},

We are pleased to offer you the position of **{{position_title}}** in our **{{department}}** department at **{{company_name}}**. We were impressed with your qualifications and believe you will be a valuable addition to our team.

## Position Details

| Item | Details |
|------|---------|
| **Position** | {{position_title}} |
| **Department** | {{department}} |
| **Reports To** | {{manager_name}} |
| **Start Date** | {{start_date}} |
| **Employment Type** | Full-time |

## Compensation

- **Annual Base Salary:** ${{salary}} USD
- **Payment Frequency:** Bi-weekly
- **Benefits:** You will be eligible for our comprehensive benefits package including health insurance, 401(k), and paid time off

## Terms

This offer is contingent upon:
1. Successful completion of background verification
2. Proof of eligibility to work in the United States
3. Signing of company policies and agreements

## Acceptance

Please indicate your acceptance by signing below and returning this letter by **{{offer_expiry_date}}**.

If you have any questions, please contact **{{hr_contact}}** in Human Resources.

We look forward to welcoming you to the team!

Sincerely,

**{{manager_name}}**  
Hiring Manager, {{department}}  
{{company_name}}

---

**ACCEPTANCE**

I, **{{candidate_name}}**, accept this offer of employment.

Signature: _________________________  
Date: _________________________
"""
        },
        
        # 4. Lease Agreement
        {
            "title": "Residential Lease Agreement",
            "doc_type": "agreement",
            "jurisdiction": "US",
            "file_description": "A residential property lease agreement between landlord and tenant with terms of rental.",
            "similarity_tags": ["lease", "rental", "property", "landlord", "tenant", "housing", "agreement"],
            "variables": [
                {"key": "landlord_name", "label": "Landlord Name", "description": "Full name of the property owner/landlord", "example": "Robert Williams", "required": True, "dtype": "string"},
                {"key": "tenant_name", "label": "Tenant Name", "description": "Full name of the tenant", "example": "Emily Davis", "required": True, "dtype": "string"},
                {"key": "property_address", "label": "Property Address", "description": "Full address of the rental property", "example": "456 Oak Street, Apt 2B, Boston, MA 02108", "required": True, "dtype": "address"},
                {"key": "lease_start_date", "label": "Lease Start Date", "description": "When the lease term begins", "example": "2025-01-01", "required": True, "dtype": "date"},
                {"key": "lease_end_date", "label": "Lease End Date", "description": "When the lease term ends", "example": "2025-12-31", "required": True, "dtype": "date"},
                {"key": "monthly_rent", "label": "Monthly Rent", "description": "Monthly rent amount in USD", "example": "2500", "required": True, "dtype": "currency"},
                {"key": "security_deposit", "label": "Security Deposit", "description": "Security deposit amount in USD", "example": "2500", "required": True, "dtype": "currency"},
                {"key": "rent_due_day", "label": "Rent Due Day", "description": "Day of month rent is due", "example": "1", "required": True, "dtype": "number"}
            ],
            "body_md": """# RESIDENTIAL LEASE AGREEMENT

---

This Lease Agreement ("Agreement") is made between:

**LANDLORD:** {{landlord_name}}  
**TENANT:** {{tenant_name}}

## 1. PROPERTY

The Landlord agrees to lease to the Tenant the property located at:

**{{property_address}}**

## 2. LEASE TERM

| Term | Details |
|------|---------|
| **Start Date** | {{lease_start_date}} |
| **End Date** | {{lease_end_date}} |
| **Type** | Fixed Term |

## 3. RENT

- **Monthly Rent:** ${{monthly_rent}}
- **Due Date:** {{rent_due_day}}th of each month
- **Late Fee:** 5% if not received within 5 days of due date
- **Payment Method:** Bank transfer or check payable to Landlord

## 4. SECURITY DEPOSIT

- **Amount:** ${{security_deposit}}
- **Due:** Upon signing of this Agreement
- **Return:** Within 30 days of lease termination, less any deductions

## 5. TENANT OBLIGATIONS

The Tenant agrees to:
1. Pay rent on time
2. Maintain the property in good condition
3. Not make alterations without written consent
4. Not sublease without prior approval
5. Comply with all applicable laws and regulations

## 6. LANDLORD OBLIGATIONS

The Landlord agrees to:
1. Maintain the property in habitable condition
2. Make necessary repairs in a timely manner
3. Provide 24-hour notice before entering (except emergencies)
4. Return security deposit as required by law

## 7. TERMINATION

Either party may terminate with 30 days written notice before the end of the lease term.

---

**SIGNATURES**

**Landlord:**  
{{landlord_name}}  
Date: _____________

**Tenant:**  
{{tenant_name}}  
Date: _____________
"""
        },
        
        # 5. Power of Attorney
        {
            "title": "General Power of Attorney",
            "doc_type": "deed",
            "jurisdiction": "US",
            "file_description": "A document authorizing one person to act on behalf of another in legal and financial matters.",
            "similarity_tags": ["power of attorney", "poa", "authorization", "legal", "agent", "principal"],
            "variables": [
                {"key": "principal_name", "label": "Principal Name", "description": "Person granting the power of attorney", "example": "James Anderson", "required": True, "dtype": "string"},
                {"key": "principal_address", "label": "Principal Address", "description": "Address of the principal", "example": "789 Pine Ave, Chicago, IL 60601", "required": True, "dtype": "address"},
                {"key": "agent_name", "label": "Agent Name", "description": "Person receiving power of attorney", "example": "Mary Anderson", "required": True, "dtype": "string"},
                {"key": "agent_address", "label": "Agent Address", "description": "Address of the agent", "example": "123 Elm Street, Chicago, IL 60602", "required": True, "dtype": "address"},
                {"key": "effective_date", "label": "Effective Date", "description": "When the POA becomes effective", "example": "2024-12-15", "required": True, "dtype": "date"},
                {"key": "expiration_date", "label": "Expiration Date", "description": "When the POA expires (leave blank for no expiration)", "example": "2025-12-15", "required": False, "dtype": "date"},
                {"key": "witness_1_name", "label": "First Witness Name", "description": "Name of first witness", "example": "John Smith", "required": True, "dtype": "string"},
                {"key": "witness_2_name", "label": "Second Witness Name", "description": "Name of second witness", "example": "Jane Doe", "required": True, "dtype": "string"}
            ],
            "body_md": """# GENERAL POWER OF ATTORNEY

---

**KNOW ALL PERSONS BY THESE PRESENTS:**

I, **{{principal_name}}**, residing at **{{principal_address}}** ("Principal"), do hereby appoint:

**{{agent_name}}**, residing at **{{agent_address}}** ("Agent")

as my true and lawful Attorney-in-Fact.

## POWERS GRANTED

I grant my Agent full power and authority to act on my behalf in the following matters:

### Financial Powers
- Access and manage bank accounts
- Make deposits and withdrawals
- Pay bills and manage debts
- File tax returns
- Manage investments

### Property Powers
- Buy, sell, or lease real property
- Manage rental properties
- Execute deeds and contracts

### Legal Powers
- Sign legal documents on my behalf
- Represent me in legal proceedings
- Settle claims and disputes

## EFFECTIVE DATE

This Power of Attorney shall become effective on **{{effective_date}}**.

## DURATION

This Power of Attorney shall remain in effect until **{{expiration_date}}**, unless revoked earlier in writing.

## REVOCATION

I reserve the right to revoke this Power of Attorney at any time by providing written notice to my Agent.

---

**PRINCIPAL SIGNATURE**

I, **{{principal_name}}**, declare that I am of sound mind and have executed this Power of Attorney voluntarily.

Signature: _________________________  
Date: _________________________

---

**WITNESSES**

We, the undersigned, witnessed the Principal sign this document:

**Witness 1:**  
Name: {{witness_1_name}}  
Signature: _________________________  
Date: _________________________

**Witness 2:**  
Name: {{witness_2_name}}  
Signature: _________________________  
Date: _________________________

---

**NOTARY ACKNOWLEDGMENT**

State of _____________  
County of _____________

On this _____ day of _____________, 20___, before me personally appeared **{{principal_name}}**, known to me to be the person whose name is subscribed to this instrument.

Notary Public: _________________________  
My Commission Expires: _____________
"""
        }
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
