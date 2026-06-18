import { apiRequest } from "./http";
import type { PrintProjectContract, PrintProjectDetail, PrintProjectSummary } from "../types/printProjects";

export interface PrintProjectExploreFilters {
  q?: string;
  file_kind?: string;
  license?: string;
  origin?: "" | "hosted" | "external";
  community?: string;
  limit?: number;
}

export const printProjectsApi = {
  contract: () => apiRequest<PrintProjectContract>("/api/print-projects/contract"),
  explore: (filters: PrintProjectExploreFilters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, String(value));
    });
    const query = params.toString();
    return apiRequest<PrintProjectSummary[]>(`/api/print-projects${query ? `?${query}` : ""}`);
  },
  detail: (slug: string) => apiRequest<PrintProjectDetail>(`/api/print-projects/${encodeURIComponent(slug)}`),
  saveReference: (projectId: number) =>
    apiRequest<PrintProjectDetail>(`/api/print-projects/${projectId}/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ save_kind: "reference" }),
    }),
  communityProjects: (slug: string) => apiRequest<PrintProjectSummary[]>(`/api/social/communities/${encodeURIComponent(slug)}/projects`),
  shareWithCommunity: (projectId: number, communitySlug: string) =>
    apiRequest<PrintProjectDetail>(`/api/print-projects/${projectId}/communities`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ community_slug: communitySlug }),
    }),
};
