/* CREATED BY UOIONHHC */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Variable {
  key: string;
  label: string;
  description?: string;
  example?: string;
  required: boolean;
  dtype: string;
}

export interface Template {
  id: number;
  template_id: string;
  title: string;
  doc_type?: string;
  jurisdiction?: string;
  file_description?: string;
  similarity_tags: string[];
  body_md: string;
  variables: Variable[];
  created_at: string;
}

export interface TemplateListItem {
  id: number;
  template_id: string;
  title: string;
  doc_type?: string;
  jurisdiction?: string;
  similarity_tags: string[];
  variable_count: number;
  created_at: string;
}

export interface UploadResponse {
  filename: string;
  extracted_text_preview: string;
  variables: Variable[];
  suggested_title: string;
  suggested_doc_type: string;
  similarity_tags: string[];
}

export interface TemplateMatchResult {
  template_id: string;
  title: string;
  score: number;
  reason: string;
  doc_type?: string;
  similarity_tags: string[];
}

export interface ChatMatchResponse {
  best_match?: TemplateMatchResult;
  alternatives: TemplateMatchResult[];
  prefilled_variables: Record<string, string>;
  missing_variables: string[];
}

export interface VariableQuestion {
  key: string;
  question: string;
  hint?: string;
  example?: string;
  required: boolean;
}

export interface DraftResponse {
  draft_id: number;
  draft_md: string;
  template_title: string;
  created_at: string;
}

// API Functions

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }
  
  return response.json();
}

export async function createTemplate(data: {
  title: string;
  body_md: string;
  variables: Variable[];
  doc_type?: string;
  jurisdiction?: string;
  file_description?: string;
  similarity_tags: string[];
}): Promise<Template> {
  const response = await fetch(`${API_BASE_URL}/api/templates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create template');
  }
  
  return response.json();
}

export async function getTemplates(): Promise<TemplateListItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/templates`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch templates');
  }
  
  return response.json();
}

export async function getTemplate(templateId: string): Promise<Template> {
  const response = await fetch(`${API_BASE_URL}/api/templates/${templateId}`);
  
  if (!response.ok) {
    throw new Error('Template not found');
  }
  
  return response.json();
}

export async function deleteTemplate(templateId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/templates/${templateId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error('Failed to delete template');
  }
}

export async function matchTemplate(query: string): Promise<ChatMatchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to match template');
  }
  
  return response.json();
}

export async function getQuestions(templateId: string, missingKeys: string[]): Promise<VariableQuestion[]> {
  const response = await fetch(`${API_BASE_URL}/api/chat/questions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ template_id: templateId, missing_keys: missingKeys }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get questions');
  }
  
  const data = await response.json();
  return data.questions;
}

export async function generateDraft(
  templateId: string,
  answers: Record<string, string>,
  userQuery?: string
): Promise<DraftResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ template_id: templateId, answers, user_query: userQuery }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate draft');
  }
  
  return response.json();
}

export async function getDrafts(): Promise<Array<{
  id: number;
  template_id: string;
  template_title: string;
  user_query: string;
  preview: string;
  created_at: string;
}>> {
  const response = await fetch(`${API_BASE_URL}/api/drafts`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch drafts');
  }
  
  return response.json();
}

export async function getDraft(draftId: number): Promise<{
  id: number;
  template_id: string;
  template_title: string;
  user_query: string;
  answers: Record<string, string>;
  draft_md: string;
  created_at: string;
}> {
  const response = await fetch(`${API_BASE_URL}/api/drafts/${draftId}`);
  
  if (!response.ok) {
    throw new Error('Draft not found');
  }
  
  return response.json();
}
