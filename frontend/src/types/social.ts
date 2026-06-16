export type CatalogTrustState = "official" | "community" | "draft" | "obsolete" | "blocked";
export type ProfileVisibility = "public" | "unlisted" | "private";
export type CommunityStatus = "active" | "uncurated" | "obsolete" | "merged";
export type RelationshipType = "follow" | "friend" | "block";
export type RelationshipStatus = "active" | "pending" | "accepted" | "ended";
export type FeedContentType = "technical_post" | "question" | "mod" | "print_result" | "file_announcement" | "curation_notice";
export type FeedOrder = "recent" | "recommended" | "pinned";
export type LibraryVisibility = "private" | "friends" | "community" | "public";
export type LibraryFileKind = "stl" | "3mf" | "bundle";
export type LibraryLicense = "cc-by" | "cc-by-sa" | "cc0" | "mit" | "custom" | "all-rights-reserved";
export type LibraryCollectionVisibility = "private" | "community" | "public";
export type PrintListItemStatus = "want_to_print" | "printed" | "problem";

export interface CatalogVariant {
  id: number;
  slug: string;
  name: string;
  build_volume: Record<string, unknown>;
  components: Record<string, unknown>;
  firmware_family: string | null;
  trust_state: CatalogTrustState;
  source: string;
}

export interface CatalogVariantDetail extends CatalogVariant {
  manufacturer_id: number;
  manufacturer_slug: string;
  manufacturer_name: string;
  model_id: number;
  model_slug: string;
  model_name: string;
  kinematics: string;
}

export interface CatalogAdminSummary {
  models: CatalogModelAdmin[];
  manufacturer_count: number;
  model_count: number;
  variant_count: number;
}

export interface CatalogModelAdmin {
  id: number;
  slug: string;
  name: string;
  kinematics: string;
  trust_state: CatalogTrustState;
  manufacturer_id: number;
  manufacturer_slug: string;
  manufacturer_name: string;
  manufacturer_website_url: string | null;
  manufacturer_repository_url: string | null;
  manufacturer_documentation_url: string | null;
  manufacturer_logo_url: string | null;
  manufacturer_discord_url: string | null;
  manufacturer_reddit_url: string | null;
  manufacturer_summary: string | null;
  website_url: string | null;
  repository_url: string | null;
  documentation_url: string | null;
  bom_url: string | null;
  image_url: string | null;
  discord_url: string | null;
  reddit_url: string | null;
  forum_url: string | null;
  description: string | null;
  curation_notes: string | null;
  detail: Record<string, unknown>;
  source_links: Record<string, unknown>;
  variants: CatalogVariant[];
}

export interface CatalogModel {
  id: number;
  slug: string;
  name: string;
  kinematics: string;
  trust_state: CatalogTrustState;
  source: string;
  variants: CatalogVariant[];
}

export interface CatalogManufacturer {
  id: number;
  slug: string;
  name: string;
  trust_state: CatalogTrustState;
  source: string;
  models: CatalogModel[];
}

export interface CatalogSummary {
  manufacturers: CatalogManufacturer[];
}

export interface PublicProfile {
  user_id: number;
  slug: string;
  display_name: string;
  bio: string | null;
  avatar_url: string | null;
  location: string | null;
  social_links: Record<string, string | null>;
  visibility: ProfileVisibility;
  created_at: string;
  updated_at: string;
  viewer_blocked?: boolean;
  reserved_slugs?: string[];
  public_printer_count?: number;
}

export interface PublicPrinter {
  id: number;
  owner_user_id: number;
  owner_slug: string | null;
  owner_display_name: string | null;
  public_name: string;
  public_description: string | null;
  public_mods: string[];
  public_images: string[];
  catalog_variant_id: number;
  manufacturer_slug: string;
  manufacturer_name: string;
  model_slug: string;
  model_name: string;
  variant_name: string;
  variant_slug: string;
  build_volume: Record<string, unknown>;
  kinematics: string;
  updated_at: string;
}

export interface Community {
  id: number;
  slug: string;
  name: string;
  scope: "manufacturer" | "model" | "variant";
  status: CommunityStatus;
  manufacturer_id: number | null;
  manufacturer_slug?: string | null;
  manufacturer_name?: string | null;
  model_id: number | null;
  model_slug?: string | null;
  model_name?: string | null;
  variant_id: number | null;
  variant_slug?: string | null;
  variant_name?: string | null;
  merged_into_id?: number | null;
  merged_into_slug?: string | null;
  merged_into_name?: string | null;
  member_count: number;
  printer_count: number;
  file_count: number;
  mod_count: number;
}

export interface CommunityDetail extends Community {
  members: PublicProfile[];
  printers: PublicPrinter[];
  filters: CatalogSummary | null;
}

export interface CommunityFeedItem {
  id: number;
  community_id: number;
  author_user_id: number | null;
  author_slug: string | null;
  author_display_name: string | null;
  content_type: FeedContentType;
  title: string;
  body: string;
  component: string | null;
  material: string | null;
  firmware_family: string | null;
  problem_tag: string | null;
  attachments: Array<{ kind: "image" | "link"; url: string; label: string }>;
  pinned: boolean;
  comment_count: number;
  reaction_count: number;
  solution_comment_id: number | null;
  edit_count: number;
  deleted_at: string | null;
  source_type: string;
  source_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CommunityFeedSummary {
  community: Community;
  items: CommunityFeedItem[];
  page: number;
  page_size: number;
  has_more: boolean;
  order: FeedOrder;
  filters: {
    components: string[];
    materials: string[];
    firmware: string[];
    problems: string[];
  };
}

export interface DiscussionComment {
  id: number;
  feed_item_id: number;
  author_user_id: number;
  author_slug: string | null;
  author_display_name: string | null;
  parent_comment_id: number | null;
  body: string;
  attachments: Array<{ kind: "image" | "link"; url: string; label: string }>;
  edit_count: number;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
  replies: DiscussionComment[];
}

export interface DiscussionReactionCount {
  reaction_type: "like" | "useful" | "thanks";
  count: number;
}

export interface DiscussionDetail {
  post: CommunityFeedItem;
  comments: DiscussionComment[];
  reactions: DiscussionReactionCount[];
}

export interface LibraryFileMetadata {
  id: number | null;
  file_kind: LibraryFileKind;
  file_name: string;
  original_url: string | null;
  size_bytes: number | null;
  sha256: string | null;
  validation_status: string;
  storage_key: string | null;
  quarantine_key: string | null;
  uploaded_size_bytes: number | null;
  rejection_reason: string | null;
  deduplicated_from_file_id: number | null;
  analysis: Record<string, unknown>;
  thumbnail_svg: string | null;
  analyzed_at: string | null;
}

export interface LibraryItem {
  id: number;
  owner_user_id: number;
  owner_slug: string | null;
  owner_display_name: string | null;
  community_id: number | null;
  community_slug: string | null;
  community_name: string | null;
  catalog_variant_id: number | null;
  manufacturer_name: string | null;
  model_name: string | null;
  variant_name: string | null;
  title: string;
  description: string;
  visibility: LibraryVisibility;
  component: string | null;
  version_label: string;
  material_suggestion: string | null;
  supports_required: boolean;
  orientation_notes: string | null;
  license: LibraryLicense;
  original_author_name: string | null;
  source_url: string | null;
  attribution_text: string | null;
  remix_source_item_id: number | null;
  remix_source_title: string | null;
  publication_terms_accepted_at: string | null;
  status: "active" | "archived";
  files: LibraryFileMetadata[];
  versions: LibraryVersion[];
  current_version_id: number | null;
  favorite_count: number;
  viewer_favorite: boolean;
  collection_count: number;
  print_list_count: number;
  download_count: number;
  created_at: string;
  updated_at: string;
}

export interface LibraryVersion {
  id: number;
  item_id: number;
  version_label: string;
  changelog: string;
  files: LibraryFileMetadata[];
  metadata_snapshot: Record<string, unknown>;
  is_current: boolean;
  created_by_user_id: number;
  created_at: string;
  download_count: number;
}

export interface LibraryCollection {
  id: number;
  owner_user_id: number;
  community_id: number | null;
  community_slug: string | null;
  community_name: string | null;
  name: string;
  description: string;
  visibility: LibraryCollectionVisibility;
  item_count: number;
  created_at: string;
  updated_at: string;
}

export interface PrintListItem {
  id: number;
  item_id: number;
  version_id: number;
  item_title: string;
  version_label: string;
  status: PrintListItemStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PrintList {
  id: number;
  owner_user_id: number;
  printer_id: number | null;
  printer_name: string | null;
  name: string;
  status: "active" | "archived";
  items: PrintListItem[];
  created_at: string;
  updated_at: string;
}

export interface LibraryDownloadHistoryItem {
  id: number;
  item_id: number;
  version_id: number | null;
  title: string;
  version_label: string | null;
  created_at: string;
}

export interface LibraryOrganizerSummary {
  favorites: LibraryItem[];
  collections: LibraryCollection[];
  print_lists: PrintList[];
  downloads: LibraryDownloadHistoryItem[];
}

export interface RelationshipRecord {
  target_user_id: number;
  target_slug: string | null;
  target_display_name: string | null;
  relation_type: RelationshipType;
  status: RelationshipStatus;
  created_at: string;
  updated_at: string;
}

export interface RelationshipSummary {
  following: RelationshipRecord[];
  followers: RelationshipRecord[];
  friends: RelationshipRecord[];
  blocked: RelationshipRecord[];
  pending_friend_requests: RelationshipRecord[];
  sent_friend_requests: RelationshipRecord[];
}
