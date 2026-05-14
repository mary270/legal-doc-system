export interface Document {
  doc_id: string;
  file_name: string;
  document_type: string;
  summary: string;
}

export interface UploadResult {
  doc_id: string;
  file_name: string;
  chunk_count: number;
  chunks_indexed: number;
  structured_fields: Record<string, string | number | boolean | null>;
}

export interface SearchResultItem {
  text: string;
  metadata: {
    file_name: string;
    doc_id: string;
  };
  relevance_score: number;
  semantic_score: number;
}

export interface SearchResult {
  results: SearchResultItem[];
}

export interface Source {
  source_number: number;
  file_name: string;
  relevance_score: number;
  excerpt: string;
}

export interface DraftResult {
  draft: string;
  sources: Source[];
  evidence_used: number;
  preferences_applied: boolean;
}

export interface EditMetrics {
  improvement_score: number;
  retained_pct: number;
  edit_distance_pct: number;
  additions_pct: number;
}

export interface FeedbackResult {
  preferences_extracted: string[];
  edit_metrics: EditMetrics;
  message: string;
}

export interface Preference {
  preference: string;
  active: boolean;
  extracted_at: string;
  improvement_score_at_capture: number;
}

export interface MetricEntry {
  timestamp: string;
  query: string;
  improvement_score: number;
  retained_pct: number;
  edit_distance_pct: number;
  changed: boolean;
}

export interface MetricsSummary {
  total_edits: number;
  avg_improvement_score: number;
  avg_retained_pct: number;
  score_trend: string;
  early_avg_score: number;
  late_avg_score: number;
}

export interface Profile {
  writing_style: string;
  structure_preferences: string;
  content_priorities: string;
  avoid: string;
  summary: string;
}

export interface FewShotExample {
  query: string;
  edited_draft: string;
  improvement_score: number;
  saved_at: string;
}
