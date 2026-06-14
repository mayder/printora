import { apiRequest } from "./http";
import type {
  CatalogSummary,
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

export const socialApi = {
  catalog: () => apiRequest<CatalogSummary>("/api/catalog"),
  myProfile: () => apiRequest<PublicProfile>("/api/social/me/profile"),
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
  communities: () => apiRequest<Community[]>("/api/social/communities"),
  community: (slug: string) => apiRequest<CommunityDetail>(`/api/social/communities/${encodeURIComponent(slug)}`),
  relationships: () => apiRequest<RelationshipSummary>("/api/social/me/relationships"),
  follow: (targetUserId: number) => apiRequest<RelationshipRecord>(`/api/social/relationships/${targetUserId}/follow`, { method: "POST" }),
  unfollow: (targetUserId: number) => apiRequest<void>(`/api/social/relationships/${targetUserId}/follow`, { method: "DELETE" }),
  requestFriend: (targetUserId: number) => apiRequest<RelationshipRecord>(`/api/social/relationships/${targetUserId}/friend-request`, { method: "POST" }),
  acceptFriend: (targetUserId: number) => apiRequest<RelationshipRecord>(`/api/social/relationships/${targetUserId}/friend-accept`, { method: "POST" }),
  block: (targetUserId: number) => apiRequest<RelationshipRecord>(`/api/social/relationships/${targetUserId}/block`, { method: "POST" }),
  unblock: (targetUserId: number) => apiRequest<void>(`/api/social/relationships/${targetUserId}/block`, { method: "DELETE" }),
};
