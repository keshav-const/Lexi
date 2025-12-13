# Lexi - Document Templatization System

A full-stack application that ingests legal documents, converts them into reusable Markdown templates with `{{variables}}`, and provides an AI-powered chat interface for drafting new documents.

<!-- CREATED BY UOIONHHC -->

## 🚀 Features

- **Document Upload**: Upload .docx/.pdf files and auto-extract variables using AI
- **Template Management**: Store templates with YAML front-matter and Markdown body
- **AI Chat Interface**: Natural language document drafting with template matching
- **Human-Friendly Q&A**: No raw variable names - polite, context-aware questions
- **Draft Generation**: Generate final Markdown documents with all variables filled
- **5 Pre-loaded Templates**: Insurance Notice, NDA, Offer Letter, Lease Agreement, Power of Attorney

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend                          │
│   ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐  │
│   │  Chat   │    │  Upload  │    │ Templates │    │  Drafts  │  │
│   └────┬────┘    └────┬─────┘    └─────┬─────┘    └────┬─────┘  │
└────────┼──────────────┼────────────────┼───────────────┼────────┘
         │              │                │               │
         └──────────────┴────────────────┴───────────────┘
                                │
                     ┌──────────▼──────────┐
                     │   FastAPI Backend    │
                     │  ┌───────────────┐   │
                     │  │ Gemini 1.5    │   │
                     │  │ Flash API     │   │
                     │  └───────────────┘   │
                     │  ┌───────────────┐   │
                     │  │ SQLite DB     │   │
                     │  └───────────────┘   │
                     └─────────────────────┘
```

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- Gemini API Key (free from [Google AI Studio](https://aistudio.google.com/))

## ⚡ Quick Start

### 1. Clone & Setup

```bash
cd e:\Lexi
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Gemini API key
echo GEMINI_API_KEY=your_key_here > .env

# Start the server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

### 4. Open the App

- Frontend: http://localhost:3000
- Backend API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
e:\Lexi\
├── backend/
│   ├── main.py              # FastAPI app with 5 sample templates
│   ├── config.py            # Configuration & env vars
│   ├── database.py          # SQLite models
│   ├── models.py            # Pydantic schemas
│   ├── services/
│   │   ├── gemini_service.py    # AI variable extraction & matching
│   │   ├── document_parser.py   # DOCX/PDF parsing
│   │   └── template_service.py  # Template CRUD
│   ├── routers/
│   │   ├── upload.py        # /api/upload endpoints
│   │   ├── templates.py     # /api/templates endpoints
│   │   ├── chat.py          # /api/chat endpoints
│   │   └── drafts.py        # /api/drafts endpoints
│   └── prompts/
│       └── templates.py     # Gemini prompt templates
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   └── lib/api.ts       # API client
│   └── package.json
└── data/
    └── lexi.db              # SQLite database (auto-created)
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload document, extract variables |
| GET/POST | `/api/templates` | List/create templates |
| GET/DELETE | `/api/templates/{id}` | Get/delete template |
| POST | `/api/chat/match` | Find matching template |
| POST | `/api/chat/questions` | Generate Q&A for variables |
| POST | `/api/chat/generate` | Generate draft |
| GET | `/api/drafts` | List draft history |

## 🎯 Usage Flow

1. **Upload a Document**
   - Go to `/upload`
   - Drop a .docx or .pdf file
   - Review detected variables
   - Save as template

2. **Draft via Chat**
   - Go to home page (Chat)
   - Type: "Draft a notice to insurer for a car accident"
   - Select the matched template
   - Answer the questions
   - Download your draft!

3. **Manage Templates**
   - Go to `/templates`
   - View, download, or delete templates
   - Export variables as JSON/CSV

## 🧠 Smart Prompts

The system uses carefully crafted prompts for:

- **Variable Extraction**: Identifies parties, dates, amounts, etc.
- **Question Generation**: Converts `policy_number` → "What is the insurance policy number exactly as it appears on your policy schedule?"
- **Template Matching**: Uses classification + embeddings for accurate matching

## 📦 Sample Templates (Pre-loaded)

1. **Incident Notice to Insurer** (India) - Insurance claims
2. **Non-Disclosure Agreement** - Confidentiality
3. **Employment Offer Letter** - Job offers
4. **Residential Lease Agreement** - Property rental
5. **General Power of Attorney** - Legal authorization

## 🔧 Environment Variables

### Backend (.env)
```
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite:///./data/lexi.db
GEMINI_MODEL=gemini-1.5-flash
```

## 📹 Demo Steps

1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Upload a sample document
4. Use chat to draft from templates
5. Download generated Markdown

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **AI**: Google Gemini 1.5 Flash

---

Built for the Full-Stack Engineer take-home assignment.
