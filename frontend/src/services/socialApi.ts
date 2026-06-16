import { apiRequest } from "./http";
import type {
  CatalogAdminSummary,
  CatalogSummary,
  CatalogTrustState,
  Community,
  CommunityDetail,
  CommunityFeedSummary,
  DiscussionComment,
  DiscussionDetail,
  FeedContentType,
  FeedOrder,
  LibraryCollectionVisibility,
  LibraryFileKind,
  LibraryItem,
  LibraryOrganizerSummary,
  LibraryLicense,
  LibraryVisibility,
  PrintListItemStatus,
  ProfileVisibility,
  PublicPrinter,
  PublicProfile,
  RelationshipRecord,
  RelationshipSummary,
  MaterialProfile,
  MaterialProfileExport,
  TechnicalConfigComparison,
  TechnicalPrinterConfig,
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

export interface CommunityPostPayload {
  content_type: FeedContentType;
  title: string;
  body: string;
  component?: string | null;
  material?: string | null;
  firmware_family?: string | null;
  problem_tag?: string | null;
  attachments?: Array<{ kind: "image" | "link"; url: string; label: string }>;
}

export interface CommunityPostUpdatePayload {
  title?: string;
  body?: string;
  attachments?: Array<{ kind: "image" | "link"; url: string; label: string }>;
}

export interface LibraryFilePayload {
  file_kind: LibraryFileKind;
  file_name: string;
  original_url?: string | null;
  size_bytes?: number | null;
  sha256?: string | null;
}

export interface LibraryItemPayload {
  title: string;
  description?: string;
  visibility: LibraryVisibility;
  community_slug?: string | null;
  catalog_variant_id?: number | null;
  component?: string | null;
  version_label?: string;
  material_suggestion?: string | null;
  supports_required?: boolean;
  orientation_notes?: string | null;
  license: LibraryLicense;
  original_author_name?: string | null;
  source_url?: string | null;
  attribution_text?: string | null;
  remix_source_item_id?: number | null;
  publication_terms_accepted?: boolean;
  files: LibraryFilePayload[];
}

export interface LibraryVersionPayload {
  version_label: string;
  changelog?: string;
  files: LibraryFilePayload[];
}

export interface LibraryCollectionPayload {
  name: string;
  description?: string;
  visibility: LibraryCollectionVisibility;
  community_slug?: string | null;
}

export interface LibraryCollectionItemPayload {
  item_id: number;
  version_id?: number | null;
  notes?: string | null;
}

export interface PrintListPayload {
  name: string;
  printer_id?: number | null;
}

export interface PrintListItemPayload {
  item_id: number;
  version_id: number;
  status?: PrintListItemStatus;
  notes?: string | null;
}

export interface TechnicalPrinterConfigPayload {
  printer_id?: number | null;
  catalog_variant_id?: number | null;
  community_slug?: string | null;
  linked_library_item_id?: number | null;
  title: string;
  visibility: "private" | "community" | "public";
  mods: string[];
  components: Record<string, string>;
  calibrations: Record<string, string>;
  notes?: string;
}

export interface MaterialProfilePayload {
  printer_id?: number | null;
  catalog_variant_id?: number | null;
  community_slug?: string | null;
  linked_library_item_id?: number | null;
  title: string;
  visibility: "private" | "community" | "public";
  material_brand?: string;
  material_type: string;
  nozzle_diameter_mm?: number | null;
  bed_temperature_c?: number | null;
  nozzle_temperature_c?: number | null;
  flow_percent?: number | null;
  notes?: string;
  version_label?: string;
  compatibility?: Record<string, string>;
  slicing: {
    layer_height_mm?: number | null;
    speed_mm_s?: number | null;
    infill_percent?: number | null;
    supports_enabled?: boolean;
    goal?: "quality" | "strength" | "speed" | "prototype";
    settings?: Record<string, string | number | boolean>;
  };
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
  communityTechnicalConfigs: (slug: string) =>
    apiRequest<TechnicalPrinterConfig[]>(`/api/social/communities/${encodeURIComponent(slug)}/technical-configs`),
  communityTechnicalComparison: (slug: string) =>
    apiRequest<TechnicalConfigComparison>(`/api/social/communities/${encodeURIComponent(slug)}/technical-configs/comparison`),
  myTechnicalConfigs: () => apiRequest<TechnicalPrinterConfig[]>("/api/social/me/technical-configs"),
  createTechnicalConfig: (payload: TechnicalPrinterConfigPayload) =>
    apiRequest<TechnicalPrinterConfig>("/api/social/technical-configs", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  updateTechnicalConfig: (configId: number, payload: TechnicalPrinterConfigPayload) =>
    apiRequest<TechnicalPrinterConfig>(`/api/social/technical-configs/${configId}`, {
      method: "PUT",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  archiveTechnicalConfig: (configId: number) => apiRequest<void>(`/api/social/technical-configs/${configId}`, { method: "DELETE" }),
  myMaterialProfiles: () => apiRequest<MaterialProfile[]>("/api/social/me/material-profiles"),
  communityMaterialProfiles: (slug: string) =>
    apiRequest<MaterialProfile[]>(`/api/social/communities/${encodeURIComponent(slug)}/material-profiles`),
  createMaterialProfile: (payload: MaterialProfilePayload) =>
    apiRequest<MaterialProfile>("/api/social/material-profiles", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  updateMaterialProfile: (profileId: number, payload: MaterialProfilePayload) =>
    apiRequest<MaterialProfile>(`/api/social/material-profiles/${profileId}`, {
      method: "PUT",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  archiveMaterialProfile: (profileId: number) => apiRequest<void>(`/api/social/material-profiles/${profileId}`, { method: "DELETE" }),
  exportMaterialProfile: (profileId: number) => apiRequest<MaterialProfileExport>(`/api/social/material-profiles/${profileId}/export`),
  importMaterialProfile: (payload: MaterialProfileExport) =>
    apiRequest<MaterialProfile>("/api/social/material-profiles/import", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  communityLibrary: (slug: string) => apiRequest<LibraryItem[]>(`/api/social/communities/${encodeURIComponent(slug)}/library`),
  profileLibrary: (slug: string) => apiRequest<LibraryItem[]>(`/api/social/profiles/${encodeURIComponent(slug)}/library`),
  libraryOrganizer: () => apiRequest<LibraryOrganizerSummary>("/api/social/me/library/organizer"),
  createLibraryCollection: (payload: LibraryCollectionPayload) =>
    apiRequest<LibraryOrganizerSummary>("/api/social/library/collections", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  addLibraryCollectionItem: (collectionId: number, payload: LibraryCollectionItemPayload) =>
    apiRequest<LibraryOrganizerSummary>(`/api/social/library/collections/${collectionId}/items`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  createPrintList: (payload: PrintListPayload) =>
    apiRequest<LibraryOrganizerSummary>("/api/social/print-lists", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  addPrintListItem: (printListId: number, payload: PrintListItemPayload) =>
    apiRequest<LibraryOrganizerSummary>(`/api/social/print-lists/${printListId}/items`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  updatePrintListItem: (printListItemId: number, payload: { status: PrintListItemStatus; notes?: string | null }) =>
    apiRequest<LibraryOrganizerSummary>(`/api/social/print-list-items/${printListItemId}`, {
      method: "PUT",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  createLibraryItem: (payload: LibraryItemPayload) =>
    apiRequest<LibraryItem>("/api/social/library", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  updateLibraryItem: (itemId: number, payload: Partial<LibraryItemPayload>) =>
    apiRequest<LibraryItem>(`/api/social/library/${itemId}`, {
      method: "PUT",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  archiveLibraryItem: (itemId: number) => apiRequest<void>(`/api/social/library/${itemId}`, { method: "DELETE" }),
  favoriteLibraryItem: (itemId: number) => apiRequest<LibraryItem>(`/api/social/library/${itemId}/favorite`, { method: "POST" }),
  unfavoriteLibraryItem: (itemId: number) => apiRequest<LibraryItem>(`/api/social/library/${itemId}/favorite`, { method: "DELETE" }),
  registerLibraryDownload: (itemId: number) => apiRequest<LibraryItem>(`/api/social/library/${itemId}/downloads`, { method: "POST" }),
  registerLibraryVersionDownload: (itemId: number, versionId: number) =>
    apiRequest<LibraryItem>(`/api/social/library/${itemId}/versions/${versionId}/downloads`, { method: "POST" }),
  createLibraryVersion: (itemId: number, payload: LibraryVersionPayload) =>
    apiRequest<LibraryItem>(`/api/social/library/${itemId}/versions`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  promoteLibraryVersion: (itemId: number, versionId: number) =>
    apiRequest<LibraryItem>(`/api/social/library/${itemId}/versions/${versionId}/current`, { method: "POST" }),
  uploadLibraryFile: (itemId: number, file: File) =>
    apiRequest<LibraryItem>(`/api/social/library/${itemId}/files/upload?file_name=${encodeURIComponent(file.name)}`, {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: file,
    }),
  analyzeLibraryFile: (fileId: number) => apiRequest<LibraryItem>(`/api/social/library/files/${fileId}/analysis`, { method: "POST" }),
  communityFeed: (
    slug: string,
    filters: {
      content_type?: FeedContentType | "";
      component?: string;
      material?: string;
      firmware_family?: string;
      problem?: string;
      order?: FeedOrder;
      page?: number;
      page_size?: number;
    } = {},
  ) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, String(value));
    });
    const query = params.toString();
    return apiRequest<CommunityFeedSummary>(`/api/social/communities/${encodeURIComponent(slug)}/feed${query ? `?${query}` : ""}`);
  },
  createCommunityPost: (slug: string, payload: CommunityPostPayload) =>
    apiRequest<CommunityFeedSummary>(`/api/social/communities/${encodeURIComponent(slug)}/posts`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  discussion: (postId: number) => apiRequest<DiscussionDetail>(`/api/social/posts/${postId}/discussion`),
  updatePost: (postId: number, payload: CommunityPostUpdatePayload) =>
    apiRequest<DiscussionDetail>(`/api/social/posts/${postId}`, {
      method: "PUT",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  deletePost: (postId: number) => apiRequest<void>(`/api/social/posts/${postId}`, { method: "DELETE" }),
  createComment: (postId: number, payload: { body: string; parent_comment_id?: number | null }) =>
    apiRequest<DiscussionComment>(`/api/social/posts/${postId}/comments`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  updateComment: (commentId: number, payload: { body: string }) =>
    apiRequest<DiscussionComment>(`/api/social/comments/${commentId}`, {
      method: "PUT",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  deleteComment: (commentId: number) => apiRequest<void>(`/api/social/comments/${commentId}`, { method: "DELETE" }),
  reactToPost: (postId: number, reactionType: "like" | "useful" | "thanks") =>
    apiRequest<void>(`/api/social/posts/${postId}/reactions`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ reaction_type: reactionType }),
    }),
  markSolution: (postId: number, commentId: number | null) => {
    const query = commentId ? `?comment_id=${commentId}` : "";
    return apiRequest<DiscussionDetail>(`/api/social/posts/${postId}/solution${query}`, { method: "POST" });
  },
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
