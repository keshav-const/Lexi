"""
Gemini AI Service for document templatization.
CREATED BY UOIONHHC

Uses dynamic model discovery to find available models.
"""
import json
import re
import httpx
from typing import Optional
import numpy as np

from config import get_settings
from prompts.templates import (
    VARIABLE_EXTRACTION_PROMPT,
    QUESTION_GENERATION_PROMPT,
    TEMPLATE_MATCHING_PROMPT,
    PREFILL_VARIABLES_PROMPT,
    TEMPLATE_GENERATION_PROMPT
)

settings = get_settings()

# Global state for discovered model
_discovered_model: Optional[str] = None
_embedding_model: Optional[str] = None
_initialized: bool = False


async def discover_models() -> tuple[str, str]:
    """
    Discover available models from the Gemini API.
    Returns (generation_model, embedding_model) tuple.
    """
    global _discovered_model, _embedding_model, _initialized
    
    if _initialized and _discovered_model:
        return _discovered_model, _embedding_model or "models/text-embedding-004"
    
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    
    print("🔍 Discovering available Gemini models...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={settings.GEMINI_API_KEY}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        
        if response.status_code != 200:
            raise ValueError(f"Failed to list models: {response.status_code} - {response.text}")
        
        data = response.json()
    
    if not data.get("models"):
        raise ValueError("No models available from Gemini API")
    
    models = data["models"]
    
    # Filter models that support generateContent
    generation_models = [
        m for m in models 
        if "generateContent" in m.get("supportedGenerationMethods", [])
    ]
    
    # Filter models that support embedContent
    embedding_models = [
        m for m in models 
        if "embedContent" in m.get("supportedGenerationMethods", [])
    ]
    
    if not generation_models:
        raise ValueError("No models found that support generateContent")
    
    # Select best generation model (prefer 1.5 flash for better free tier limits)
    selected_model = None
    
    # Priority order for model selection - prefer 1.5-flash (more stable free tier)
    model_preferences = [
        "gemini-1.5-flash",  # Most reliable free tier
        "gemini-1.5-pro",
        "gemini-flash",
        "gemini-pro",
    ]
    
    for pref in model_preferences:
        for m in generation_models:
            name = m.get("name", "")
            if pref in name and "exp" not in name and "thinking" not in name:
                selected_model = m
                break
        if selected_model:
            break
    
    if not selected_model:
        selected_model = generation_models[0]
    
    _discovered_model = selected_model["name"]
    
    # Select embedding model
    if embedding_models:
        # Prefer text-embedding-004
        for m in embedding_models:
            if "text-embedding" in m.get("name", ""):
                _embedding_model = m["name"]
                break
        if not _embedding_model:
            _embedding_model = embedding_models[0]["name"]
    else:
        _embedding_model = "models/text-embedding-004"
    
    _initialized = True
    
    print(f"✅ Selected generation model: {selected_model.get('displayName', _discovered_model)}")
    print(f"✅ Selected embedding model: {_embedding_model}")
    print(f"📊 Available generation models: {[m.get('displayName', m['name']) for m in generation_models[:5]]}")
    
    return _discovered_model, _embedding_model


def clean_json_response(response_text: str) -> str:
    """Clean Gemini response to extract valid JSON."""
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def call_gemini(prompt: str, max_tokens: int = 2048, max_retries: int = 3) -> str:
    """
    Call the Gemini API with the given prompt.
    Uses dynamically discovered model with retry logic for rate limits.
    """
    import asyncio
    import re as regex_module
    
    model_name, _ = await discover_models()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
    
    request_body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": max_tokens,
        }
    }
    
    last_error = None
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=request_body,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if not data.get("candidates") or not data["candidates"][0].get("content"):
                        raise ValueError("Invalid response format from Gemini API")
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                
                elif response.status_code == 429:
                    # Rate limit - parse retry delay if available
                    error_text = response.text
                    retry_delay = 5 * (2 ** attempt)  # Default exponential backoff
                    
                    # Try to parse retry delay from response
                    match = regex_module.search(r'retry in (\d+\.?\d*)s', error_text, regex_module.IGNORECASE)
                    if match:
                        retry_delay = max(float(match.group(1)), retry_delay)
                    
                    print(f"⏳ Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay:.1f}s...")
                    await asyncio.sleep(retry_delay)
                    last_error = ValueError(f"Rate limit exceeded: {error_text[:200]}")
                    
                else:
                    raise ValueError(f"Gemini API error: {response.status_code} - {response.text[:500]}")
                    
        except httpx.TimeoutException:
            print(f"⏳ Request timeout (attempt {attempt + 1}/{max_retries}). Retrying...")
            last_error = ValueError("Request timed out")
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            if "429" not in str(e) and "rate" not in str(e).lower():
                raise
            last_error = e
            await asyncio.sleep(5 * (2 ** attempt))
    
    raise last_error or ValueError("Max retries exceeded")


async def extract_variables(document_text: str) -> dict:
    """
    Extract variables from document text using Gemini.
    
    Returns:
        dict with keys: title, doc_type, file_description, similarity_tags, variables
    """
    # Chunk long documents (>10k chars)
    if len(document_text) > 10000:
        return await extract_variables_chunked(document_text)
    
    prompt = VARIABLE_EXTRACTION_PROMPT.format(document_text=document_text)
    
    response_text = await call_gemini(prompt)
    response_text = clean_json_response(response_text)
    
    try:
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError as e:
        # Try to fix common JSON issues
        try:
            fixed = re.sub(r',\s*}', '}', response_text)
            fixed = re.sub(r',\s*]', ']', fixed)
            result = json.loads(fixed)
            return result
        except:
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}")


async def extract_variables_chunked(document_text: str, chunk_size: int = 8000) -> dict:
    """Extract variables from long documents using chunking strategy."""
    chunks = [document_text[i:i+chunk_size] for i in range(0, len(document_text), chunk_size)]
    
    all_variables = []
    seen_keys = set()
    title = ""
    doc_type = ""
    file_description = ""
    similarity_tags = []
    
    for i, chunk in enumerate(chunks):
        if i == 0:
            prompt = VARIABLE_EXTRACTION_PROMPT.format(document_text=chunk)
        else:
            existing_vars_json = json.dumps([v for v in all_variables], indent=2)
            prompt = f"""You are continuing to extract variables from a long document.

## Previously discovered variables (DO NOT duplicate these):
{existing_vars_json}

## Instructions:
1. Only identify NEW variables not in the above list
2. Reuse existing keys for logically identical fields
3. Same output format as before

## Document Chunk {i+1}:
{chunk}

Return JSON with only NEW variables (or empty variables array if none):
"""
        
        response_text = await call_gemini(prompt)
        response_text = clean_json_response(response_text)
        
        try:
            result = json.loads(response_text)
            
            if i == 0:
                title = result.get("title", "")
                doc_type = result.get("doc_type", "")
                file_description = result.get("file_description", "")
                similarity_tags = result.get("similarity_tags", [])
            
            for var in result.get("variables", []):
                if var["key"] not in seen_keys:
                    all_variables.append(var)
                    seen_keys.add(var["key"])
        except json.JSONDecodeError:
            continue
    
    return {
        "title": title,
        "doc_type": doc_type,
        "file_description": file_description,
        "similarity_tags": similarity_tags,
        "variables": all_variables
    }


async def generate_questions(variables: list[dict]) -> list[dict]:
    """
    Generate human-friendly questions for variables.
    """
    if not variables:
        return []
    
    variables_json = json.dumps(variables, indent=2)
    prompt = QUESTION_GENERATION_PROMPT.format(variables_json=variables_json)
    
    response_text = await call_gemini(prompt)
    response_text = clean_json_response(response_text)
    
    try:
        questions = json.loads(response_text)
        return questions
    except json.JSONDecodeError:
        # Fallback: generate basic questions
        return [
            {
                "key": v["key"],
                "question": f"Please provide the {v.get('label', v['key'])}:",
                "hint": v.get("description", ""),
                "example": v.get("example", ""),
                "required": v.get("required", True)
            }
            for v in variables
        ]


async def match_template(user_query: str, templates: list[dict]) -> dict:
    """
    Find the best matching template for a user query.
    """
    if not templates:
        return {"matches": [], "no_match_reason": "No templates available in database"}
    
    templates_json = json.dumps(templates, indent=2)
    prompt = TEMPLATE_MATCHING_PROMPT.format(
        user_query=user_query,
        templates_json=templates_json
    )
    
    response_text = await call_gemini(prompt)
    response_text = clean_json_response(response_text)
    
    try:
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        return {"matches": [], "no_match_reason": "Failed to parse matching response"}


async def prefill_variables(user_query: str, variables: list[dict]) -> dict:
    """
    Extract variable values from user query.
    """
    if not variables:
        return {"prefilled": {}, "confidence": {}}
    
    variables_json = json.dumps(variables, indent=2)
    prompt = PREFILL_VARIABLES_PROMPT.format(
        user_query=user_query,
        variables_json=variables_json
    )
    
    response_text = await call_gemini(prompt)
    response_text = clean_json_response(response_text)
    
    try:
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        return {"prefilled": {}, "confidence": {}}


async def generate_template_body(document_text: str, variables: list[dict]) -> str:
    """
    Generate the Markdown template body with {{variables}}.
    """
    variables_json = json.dumps(variables, indent=2)
    prompt = TEMPLATE_GENERATION_PROMPT.format(
        document_text=document_text,
        variables_json=variables_json
    )
    
    return await call_gemini(prompt)


async def generate_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for text using Gemini embedding model.
    """
    _, embedding_model = await discover_models()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{embedding_model}:embedContent?key={settings.GEMINI_API_KEY}"
    
    request_body = {
        "model": embedding_model,
        "content": {
            "parts": [{"text": text}]
        },
        "taskType": "RETRIEVAL_DOCUMENT"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=request_body,
            timeout=30.0
        )
        
        if response.status_code != 200:
            # Fallback: return empty embedding if embedding fails
            print(f"⚠️ Embedding failed: {response.status_code} - {response.text}")
            return []
        
        data = response.json()
    
    if "embedding" in data and "values" in data["embedding"]:
        return data["embedding"]["values"]
    
    return []


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not a or not b:
        return 0.0
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
