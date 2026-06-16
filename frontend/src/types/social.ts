export type CatalogTrustState = "official" | "community" | "draft" | "obsolete" | "blocked";
export type ProfileVisibility = "public" | "unlisted" | "private";
export type CommunityStatus = "active" | "uncurated" | "obsolete" | "merged";
export type RelationshipType = "follow" | "friend" | "block";
export type RelationshipStatus = "active" | "pending" | "accepted" | "ended";
export type FeedContentType = "technical_post" | "question" | "mod" | "print_result" | "file_announcement" | "curation_notice";
export type FeedOrder = "recent" | "recommended" | "pinned";

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
