import type { ChangeItem, Overview, Publication, Source } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}/api/v1${path}`);
  if (!response.ok) throw new Error(`API request failed (${response.status}) for ${path}`);
  return response.json() as Promise<T>;
}

export const api = {
  overview: () => request<Overview>("/overview"),
  publications: () => request<{ items: Publication[]; total: number }>("/publications"),
  changes: () => request<{ items: ChangeItem[]; total: number }>("/changes"),
  sources: () => request<{ items: Source[]; total: number }>("/sources"),
};
