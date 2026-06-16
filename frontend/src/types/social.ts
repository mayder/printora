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
export type SearchEntityType = "community" | "post" | "library_item" | "technical_config" | "material_profile" | "catalog_variant";
export type SearchOrder = "relevance" | "recent" | "popular";
export type ModerationEntityType = "post" | "comment" | "profile" | "library_item" | "catalog_variant" | "community" | "tag";
export type ModerationReason = "spam" | "unsafe" | "illegal" | "harassment" | "privacy" | "wrong_metadata" | "other";
export type ModerationReportStatus = "open" | "reviewing" | "resolved" | "dismissed";
export type ModerationAction = "mark_reviewing" | "hide" | "remove" | "block" | "restore" | "dismiss" | "curate";
export type SocialNotificationType = "comment" | "reaction" | "solution" | "follow" | "friend_request" | "friend_accept" | "content_update" | "community_post" | "digest";
export type SocialNotificationStatus = "unread" | "read" | "archived";
export type ContentFollowEntityType = "post" | "library_item" | "catalog_variant" | "community" | "collection";
export type FollowersVisibility = "public" | "followers" | "friends" | "private";
export type SocialMessagesFrom = "public" | "followers" | "friends" | "none";
export type AbuseSignalStatus = "active" | "reviewing" | "resolved" | "dismissed";

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

export interface SocialSafetySettings {
  user_id: number;
  profile_discoverable: boolean;
  followers_visibility: FollowersVisibility;
  messages_from: SocialMessagesFrom;
  allow_content_mentions: boolean;
  allow_download_tracking: boolean;
  updated_at: string;
}

export interface AbuseSignalRecord {
  id: number;
  subject_user_id: number | null;
  target_user_id: number | null;
  action: string;
  reason: string;
  severity: number;
  status: AbuseSignalStatus;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface SocialSafetyStatus {
  settings: SocialSafetySettings;
  recent_denials: number;
  active_signals: AbuseSignalRecord[];
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
  manufacturer_logo_url?: string | null;
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

export interface TechnicalPrinterConfig {
  id: number;
  owner_user_id: number;
  owner_slug: string | null;
  owner_display_name: string | null;
  printer_id: number | null;
  printer_public_name: string | null;
  catalog_variant_id: number | null;
  manufacturer_name: string | null;
  model_name: string | null;
  variant_name: string | null;
  community_slug: string | null;
  community_id: number | null;
  community_name: string | null;
  linked_library_item_id: number | null;
  title: string;
  visibility: "private" | "community" | "public";
  mods: string[];
  components: Record<string, string>;
  calibrations: Record<string, string>;
  notes: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TechnicalConfigComparison {
  community_slug: string;
  community_name: string;
  configs: TechnicalPrinterConfig[];
  normalized_components: Record<string, string[]>;
  normalized_calibrations: Record<string, string[]>;
}

export interface SlicingProfile {
  id: number;
  material_profile_id: number;
  layer_height_mm: number | null;
  speed_mm_s: number | null;
  infill_percent: number | null;
  supports_enabled: boolean;
  goal: "quality" | "strength" | "speed" | "prototype";
  settings: Record<string, string | number | boolean>;
  created_at: string;
  updated_at: string;
}

export interface MaterialProfile {
  id: number;
  owner_user_id: number;
  owner_slug: string | null;
  owner_display_name: string | null;
  printer_id: number | null;
  printer_public_name: string | null;
  catalog_variant_id: number | null;
  manufacturer_name: string | null;
  model_name: string | null;
  variant_name: string | null;
  community_slug: string | null;
  community_id: number | null;
  community_name: string | null;
  linked_library_item_id: number | null;
  title: string;
  visibility: "private" | "community" | "public";
  material_brand: string;
  material_type: string;
  nozzle_diameter_mm: number | null;
  bed_temperature_c: number | null;
  nozzle_temperature_c: number | null;
  flow_percent: number | null;
  notes: string;
  version_label: string;
  compatibility: Record<string, string>;
  slicing: SlicingProfile;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface MaterialProfileExport {
  format: "printora.material-profile.v1";
  profile: MaterialProfile;
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

export interface StoragePolicy {
  scope_type: string;
  scope_id: number | null;
  quota_bytes: number;
  retention_days: number;
  cost_per_gb_month_cents: number;
}

export interface StorageUsageSummary {
  quota_bytes: number;
  used_bytes: number;
  remaining_bytes: number;
  projected_monthly_cost_cents: number;
  file_count: number;
  deduplicated_file_count: number;
  active_item_count: number;
  archived_item_count: number;
}

export interface StorageRetentionCandidate {
  file_id: number;
  item_id: number;
  file_name: string;
  size_bytes: number;
  status: string;
  referenced_by_current_version: boolean;
  eligible: boolean;
  reason: string;
}

export interface StorageRetentionPlan {
  mode: "dry_run";
  retention_days: number;
  candidate_count: number;
  blocked_count: number;
  reclaimable_bytes: number;
  candidates: StorageRetentionCandidate[];
  review_id: number | null;
}

export interface StorageReport {
  policy: StoragePolicy;
  usage: StorageUsageSummary;
  retention: StorageRetentionPlan;
  object_storage_plan: string[];
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

export interface SearchResult {
  entity_type: SearchEntityType;
  entity_id: number;
  title: string;
  summary: string;
  tags: string[];
  community_slug: string | null;
  community_name: string | null;
  manufacturer_name: string | null;
  model_name: string | null;
  variant_name: string | null;
  owner_slug: string | null;
  owner_display_name: string | null;
  material_type: string | null;
  component: string | null;
  license: string | null;
  file_kind: string | null;
  popularity_score: number;
  updated_at: string;
  url: string;
}

export interface SearchFacetOption {
  value: string;
  label: string;
  count: number;
}

export interface SearchFacets {
  entity_types: SearchFacetOption[];
  tags: SearchFacetOption[];
  communities: SearchFacetOption[];
  materials: SearchFacetOption[];
  components: SearchFacetOption[];
  licenses: SearchFacetOption[];
  file_kinds: SearchFacetOption[];
}

export interface SearchResponse {
  query: string;
  page: number;
  page_size: number;
  has_more: boolean;
  results: SearchResult[];
  facets: SearchFacets;
  indexed_count: number;
}

export interface ModerationReport {
  id: number;
  entity_type: ModerationEntityType;
  entity_id: number;
  reporter_user_id: number | null;
  reporter_display_name: string | null;
  reason: ModerationReason;
  detail: string;
  status: ModerationReportStatus;
  assigned_moderator_user_id: number | null;
  resolution_note: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  entity_title: string | null;
  entity_status: string | null;
}

export interface ModerationActionRecord {
  id: number;
  report_id: number | null;
  entity_type: ModerationEntityType;
  entity_id: number;
  action: ModerationAction;
  previous_state: Record<string, unknown>;
  new_state: Record<string, unknown>;
  moderator_user_id: number | null;
  reason: string;
  created_at: string;
}

export interface ModerationQueue {
  reports: ModerationReport[];
  actions: ModerationActionRecord[];
}

export interface SocialNotification {
  id: number;
  recipient_user_id: number;
  actor_user_id: number | null;
  actor_display_name: string | null;
  notification_type: SocialNotificationType;
  entity_type: string;
  entity_id: number;
  title: string;
  body: string;
  action_url: string | null;
  status: SocialNotificationStatus;
  metadata: Record<string, unknown>;
  created_at: string;
  read_at: string | null;
}

export interface NotificationPreference {
  notification_type: SocialNotificationType;
  in_app_enabled: boolean;
  digest_enabled: boolean;
}

export interface ContentFollow {
  id: number;
  user_id: number;
  entity_type: ContentFollowEntityType;
  entity_id: number;
  muted: boolean;
  digest_enabled: boolean;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface NotificationCenter {
  notifications: SocialNotification[];
  unread_count: number;
  preferences: NotificationPreference[];
  follows: ContentFollow[];
  digest: SocialNotification[];
}

export interface TagRecord {
  slug: string;
  label: string;
  status: string;
  source: string;
}

export interface RecommendationItem {
  result: SearchResult;
  score: number;
  reasons: string[];
  contributor_reputation: number;
}

export interface RecommendationResponse {
  items: RecommendationItem[];
  indexed_count: number;
  scoring: Record<string, number>;
}

export interface ReputationRecord {
  user_id: number;
  slug: string | null;
  display_name: string | null;
  contribution_count: number;
  reputation_score: number;
  breakdown: Record<string, number>;
}

export interface ReputationResponse {
  records: ReputationRecord[];
}
