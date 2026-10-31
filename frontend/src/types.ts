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
