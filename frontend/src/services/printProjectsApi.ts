import { apiRequest } from "./http";
import type { PrintProjectContract, PrintProjectSummary } from "../types/printProjects";

export const printProjectsApi = {
  contract: () => apiRequest<PrintProjectContract>("/api/print-projects/contract"),
  explore: (filters: { q?: string; limit?: number } = {}) => {
    const params = new URLSearchParams();
    if (filters.q) params.set("q", filters.q);
    if (filters.limit) params.set("limit", String(filters.limit));
    const query = params.toString();
    return apiRequest<PrintProjectSummary[]>(`/api/print-projects${query ? `?${query}` : ""}`);
  },
};
