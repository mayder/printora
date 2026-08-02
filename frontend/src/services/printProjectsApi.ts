import { apiInput, apiRequest, apiResponse, readApiError } from "./http";
import type {
  PrintProjectCreatePayload,
  PrintProjectContract,
  PrintProjectDetail,
  PrintProjectExternalLinkPayload,
  PrintProjectFileRole,
  PrintProjectFileStructurePayload,
  PrintProjectPublicationPayload,
  PrintProjectStorageReport,
  PrintProjectSummary,
  PrintProjectUpdatePayload,
} from "../types/printProjects";

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
  myProjects: () => apiRequest<PrintProjectSummary[]>("/api/print-projects/me"),
  storage: () => apiRequest<PrintProjectStorageReport>("/api/print-projects/me/storage"),
  create: (payload: PrintProjectCreatePayload) =>
    apiRequest<PrintProjectDetail>("/api/print-projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  update: (projectId: number, payload: PrintProjectUpdatePayload) =>
    apiRequest<PrintProjectDetail>(`/api/print-projects/${projectId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  archive: (projectId: number) =>
    apiRequest<{ ok: boolean }>(`/api/print-projects/${projectId}`, {
      method: "DELETE",
    }),
  updatePublication: (projectId: number, payload: PrintProjectPublicationPayload) =>
    apiRequest<PrintProjectDetail>(`/api/print-projects/${projectId}/publication`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  uploadFile: (projectId: number, file: File, fileRole: PrintProjectFileRole) =>
    apiRequest<PrintProjectDetail>(
      `/api/print-projects/${projectId}/files/upload?file_name=${encodeURIComponent(file.name)}&file_role=${encodeURIComponent(fileRole)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/octet-stream", "Idempotency-Key": crypto.randomUUID() },
        body: file,
      },
    ),
  updateFileStructure: (projectId: number, fileId: number, payload: PrintProjectFileStructurePayload) =>
    apiRequest<PrintProjectDetail>(`/api/print-projects/${projectId}/files/${fileId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  fileBlob: async (fileId: number) => {
    const token = await apiRequest<{ download_url: string; authorization_token: string }>(`/api/storage/print-project-files/${fileId}/tokens`, { method: "POST" });
    const response = await fetch(apiInput(token.download_url), { headers: { Authorization: `Bearer ${token.authorization_token}` } });
    if (!response.ok) throw new Error(await readApiError(response));
    return response.blob();
  },
  bundleBlob: async (projectId: number) => {
    const response = await apiResponse(`/api/print-projects/${projectId}/bundle`);
    if (!response.ok) throw new Error(await readApiError(response));
    return response.blob();
  },
  addExternalLink: (projectId: number, payload: PrintProjectExternalLinkPayload) =>
    apiRequest<PrintProjectDetail>(`/api/print-projects/${projectId}/external-links`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
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
