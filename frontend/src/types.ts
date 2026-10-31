export interface Publication {
  id: string; title: string; authority: string; country: string; area: string;
  published: string; effective: string; status: string; kind: string;
}
export interface ChangeItem {
  id: string; publication: string; country: string; classification: string;
  priority: string; previous: string; updated: string; impact: string;
  actions: string[]; source: string;
}
export interface Overview {
  total_publications: number; new_or_unreviewed: number; awaiting_review: number;
  regions_represented: number; coverage: { country: string; count: number }[];
  recent_publications: Publication[];
}
export interface Source { country: string; authority: string; region: string; status: string; }

export interface ExtractedObligation {
  requirement: string;
  classification: string;
  applies_to: string[];
  deadline: string;
  source_reference: string;
  source_excerpt: string;
  evidence_verified: boolean;
}
export interface GeminiDiagnostics {
  configured: boolean;
  model: string;
  key_source: string;
  local_env_files_found: string[];
}
export interface DocumentAnalysis {
  publication: Publication;
  document: {
    filename: string;
    extension: string;
    size_bytes: number;
    text_characters: number;
    source_sections: number;
    sha256: string;
  };
  extraction: {
    method: string;
    gemini_status: "not_configured" | "used" | "failed";
    model: string | null;
    summary: string;
    metadata: Record<string, string>;
    obligations: ExtractedObligation[];
    obligation_count: number;
    note: string;
  };
}
