import type {
  Document,
  UploadResult,
  SearchResult,
  DraftResult,
  FeedbackResult,
  Preference,
  MetricEntry,
  MetricsSummary,
  Profile,
  FewShotExample,
} from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const body = await res.json();
      if (body.detail) errorMsg = body.detail;
      else if (body.message) errorMsg = body.message;
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMsg);
  }
  return res.json() as Promise<T>;
}

// Health
export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${BASE_URL}/health`);
  return handleResponse(res);
}

// Documents
export async function getDocuments(): Promise<Document[]> {
  const res = await fetch(`${BASE_URL}/documents`);
  return handleResponse<Document[]>(res);
}

export async function uploadDocument(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<UploadResult>(res);
}

export async function deleteDocument(docId: string): Promise<{ chunks_removed: number }> {
  const res = await fetch(`${BASE_URL}/documents/${docId}`, {
    method: 'DELETE',
  });
  return handleResponse<{ chunks_removed: number }>(res);
}

// Retrieval / Search
export async function searchDocuments(
  query: string,
  nResults: number = 8,
  docIdFilter?: string | null
): Promise<SearchResult> {
  const params: Record<string, string> = {
    query,
    n_results: String(nResults),
  };
  if (docIdFilter) params.doc_id_filter = docIdFilter;

  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE_URL}/retrieval/search?${qs}`, {
    method: 'POST',
  });
  return handleResponse<SearchResult>(res);
}

// Drafts
export async function generateDraft(
  query: string,
  nResults: number = 8,
  docIdFilter?: string | null,
  useFewShot: boolean = true,
  useProfile: boolean = true
): Promise<DraftResult> {
  const body: Record<string, unknown> = {
    query,
    n_results: nResults,
    use_few_shot: useFewShot,
    use_profile: useProfile,
  };
  if (docIdFilter) body.doc_id_filter = docIdFilter;

  const res = await fetch(`${BASE_URL}/drafts/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return handleResponse<DraftResult>(res);
}

export async function submitFeedback(
  originalDraft: string,
  editedDraft: string,
  query: string,
  docNames: string[]
): Promise<FeedbackResult> {
  const res = await fetch(`${BASE_URL}/drafts/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      original_draft: originalDraft,
      edited_draft: editedDraft,
      query,
      doc_names: docNames,
    }),
  });
  return handleResponse<FeedbackResult>(res);
}

// Preferences
export async function getActivePreferences(): Promise<{ preferences: string[] }> {
  const res = await fetch(`${BASE_URL}/preferences/active`);
  return handleResponse<{ preferences: string[] }>(res);
}

export async function getAllPreferences(): Promise<Preference[]> {
  const res = await fetch(`${BASE_URL}/preferences`);
  return handleResponse<Preference[]>(res);
}

export async function deactivatePreference(index: number): Promise<{ deactivated: boolean; index: number }> {
  const res = await fetch(`${BASE_URL}/preferences/deactivate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ index }),
  });
  return handleResponse<{ deactivated: boolean; index: number }>(res);
}

// Metrics
export async function getMetrics(): Promise<MetricEntry[]> {
  const res = await fetch(`${BASE_URL}/metrics`);
  return handleResponse<MetricEntry[]>(res);
}

export async function getMetricsSummary(): Promise<MetricsSummary> {
  const res = await fetch(`${BASE_URL}/metrics/summary`);
  return handleResponse<MetricsSummary>(res);
}

// Profile
export async function getProfile(): Promise<Profile> {
  const res = await fetch(`${BASE_URL}/profile`);
  return handleResponse<Profile>(res);
}

export async function buildProfile(): Promise<{ message?: string; status?: string }> {
  const res = await fetch(`${BASE_URL}/profile/build`, {
    method: 'POST',
  });
  return handleResponse<{ message?: string; status?: string }>(res);
}

// Few-shot examples
export async function getFewShotExamples(): Promise<FewShotExample[]> {
  const res = await fetch(`${BASE_URL}/few-shot`);
  return handleResponse<FewShotExample[]>(res);
}
