import type { ChangeItem, DocumentAnalysis, GeminiDiagnostics, Overview, Publication, Source } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}/api/v1${path}`);
  if (!response.ok) throw new Error(`API request failed (${response.status}) for ${path}`);
  return response.json() as Promise<T>;
}

async function analyzeDocument(file: File): Promise<DocumentAnalysis> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${API_BASE}/api/v1/documents/analyze`, {
    method: "POST",
    body,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail ?? `Document analysis failed (${response.status}).`);
  }
  return payload as DocumentAnalysis;
}

export const api = {
  overview: () => request<Overview>("/overview"),
  publications: () => request<{ items: Publication[]; total: number }>("/publications"),
  changes: () => request<{ items: ChangeItem[]; total: number }>("/changes"),
  sources: () => request<{ items: Source[]; total: number }>("/sources"),
  geminiDiagnostics: () => request<GeminiDiagnostics>("/diagnostics/gemini"),
  analyzeDocument,
};
