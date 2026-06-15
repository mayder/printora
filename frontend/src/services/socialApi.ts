import { apiRequest } from "./http";
import type {
  CatalogAdminSummary,
  CatalogSummary,
  CatalogTrustState,
  Community,
  CommunityDetail,
  ProfileVisibility,
  PublicPrinter,
  PublicProfile,
  RelationshipRecord,
  RelationshipSummary,
} from "../types";

const jsonHeaders = { "Content-Type": "application/json" };

export interface ProfilePayload {
  slug?: string | null;
  display_name: string;
  bio?: string | null;
  avatar_url?: string | null;
  location?: string | null;
  social_links?: Record<string, string | null>;
  visibility: ProfileVisibility;
}

export interface PrinterPublicPayload {
  public_profile_enabled: boolean;
  catalog_variant_id?: number | null;
  public_name?: string | null;
  public_description?: string | null;
  public_mods?: string[];
  public_images?: string[];
}

export interface CatalogAdminFilters {
  manufacturer?: string;
  model?: string;
  variant?: string;
  component?: string;
  kinematics?: string;
  firmware_family?: string;
  trust_state?: CatalogTrustState | "";
}

export interface CatalogVariantUpdatePayload {
  name?: string;
  build_volume?: Record<string, unknown>;
  components?: Record<string, unknown>;
  firmware_family?: string | null;
  trust_state?: CatalogTrustState;
  source?: string;
}

export interface CatalogVariantCreatePayload {
  model_id: number;
  name: string;
  slug?: string | null;
  build_volume?: Record<string, unknown>;
  components?: Record<string, unknown>;
  firmware_family?: string | null;
  trust_state?: CatalogTrustState;
  source?: string;
}

export const socialApi = {
  catalog: () => apiRequest<CatalogSummary>("/api/catalog"),
  adminCatalog: (filters: CatalogAdminFilters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, String(value));
    });
    const query = params.toString();
    return apiRequest<CatalogAdminSummary>(`/api/catalog/admin${query ? `?${query}` : ""}`);
  },
  updateCatalogVariant: (variantId: number, payload: CatalogVariantUpdatePayload) =>
    apiRequest(`/api/catalog/variants/${variantId}`, {
      method: "PUT",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  createCatalogVariant: (payload: CatalogVariantCreatePayload) =>
    apiRequest(`/api/catalog/variants`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  myProfile: () => apiRequest<PublicProfile>("/api/social/me/profile"),
  publicProfile: (slug: string) => apiRequest<PublicProfile>(`/api/social/profiles/${encodeURIComponent(slug)}`),
  searchProfiles: (query: string) => apiRequest<PublicProfile[]>(`/api/social/profiles?q=${encodeURIComponent(query)}`),
  publicPrinter: (printerId: number | string) => apiRequest<PublicPrinter>(`/api/public/printers/${encodeURIComponent(String(printerId))}`),
  publicPrinters: (filters: { manufacturer?: string; model?: string; variant?: string; mod?: string } = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    const query = params.toString();
    return apiRequest<PublicPrinter[]>(`/api/social/printers${query ? `?${query}` : ""}`);
  },
  updateProfile: (payload: ProfilePayload) =>
    apiRequest<PublicProfile>("/api/social/me/profile", {
      method: "PUT",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  profilePrinters: (slug: string) => apiRequest<PublicPrinter[]>(`/api/social/profiles/${encodeURIComponent(slug)}/printers`),
  updatePrinterPublic: (printerId: number, payload: PrinterPublicPayload) =>
    apiRequest<PublicPrinter | null>(`/api/printers/${printerId}/public-profile`, {
      method: "PUT",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  communities: (filters: { manufacturer?: string; model?: string; variant?: string; component?: string } = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    const query = params.toString();
    return apiRequest<Community[]>(`/api/social/communities${query ? `?${query}` : ""}`);
  },
  community: (slug: string) => apiRequest<CommunityDetail>(`/api/social/communities/${encodeURIComponent(slug)}`),
  relationships: () => apiRequest<RelationshipSummary>("/api/social/me/relationships"),
  follow: (targetUserId: number) => apiRequest<RelationshipRecord>(`/api/social/relationships/${targetUserId}/follow`, { method: "POST" }),
  unfollow: (targetUserId: number) => apiRequest<void>(`/api/social/relationships/${targetUserId}/follow`, { method: "DELETE" }),
  requestFriend: (targetUserId: number) => apiRequest<RelationshipRecord>(`/api/social/relationships/${targetUserId}/friend-request`, { method: "POST" }),
  cancelFriendRequest: (targetUserId: number) => apiRequest<void>(`/api/social/relationships/${targetUserId}/friend-request`, { method: "DELETE" }),
  acceptFriend: (targetUserId: number) => apiRequest<RelationshipRecord>(`/api/social/relationships/${targetUserId}/friend-accept`, { method: "POST" }),
  rejectFriend: (targetUserId: number) => apiRequest<void>(`/api/social/relationships/${targetUserId}/friend-reject`, { method: "POST" }),
  unfriend: (targetUserId: number) => apiRequest<void>(`/api/social/relationships/${targetUserId}/friend`, { method: "DELETE" }),
  block: (targetUserId: number) => apiRequest<RelationshipRecord>(`/api/social/relationships/${targetUserId}/block`, { method: "POST" }),
  unblock: (targetUserId: number) => apiRequest<void>(`/api/social/relationships/${targetUserId}/block`, { method: "DELETE" }),
};
