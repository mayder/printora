export type CatalogTrustState = "official" | "community" | "draft" | "obsolete" | "blocked";
export type ProfileVisibility = "public" | "unlisted" | "private";
export type CommunityStatus = "active" | "uncurated" | "obsolete" | "merged";
export type RelationshipType = "follow" | "friend" | "block";
export type RelationshipStatus = "active" | "pending" | "accepted" | "ended";

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
  website_url: string | null;
  repository_url: string | null;
  documentation_url: string | null;
  bom_url: string | null;
  description: string | null;
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
  manufacturer_name: string;
  model_name: string;
  variant_name: string;
  variant_slug: string;
  updated_at: string;
}

export interface Community {
  id: number;
  slug: string;
  name: string;
  scope: "manufacturer" | "model" | "variant";
  status: CommunityStatus;
  manufacturer_id: number | null;
  model_id: number | null;
  variant_id: number | null;
  member_count: number;
  printer_count: number;
}

export interface CommunityDetail extends Community {
  members: PublicProfile[];
  printers: PublicPrinter[];
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
}
