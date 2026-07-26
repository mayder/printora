export type DesignState =
  | "loading"
  | "empty"
  | "error"
  | "success"
  | "partial"
  | "offline"
  | "forbidden"
  | "conflict";

export type DesignDensity = "workshop" | "reading" | "administration";
export type DesignCollectionMode = "cards" | "table" | "gallery";

export type DesignToken = {
  name: string;
  value: string;
  purpose: string;
};

export type DesignCapability = {
  capability_id: string;
  com_ids: string[];
  screen_id: string;
  slug: string;
  title: string;
  summary: string;
  route: string;
  tokens: DesignToken[];
  supported_states: DesignState[];
};

export type DesignSystemCatalog = {
  contract_version: string;
  compatible_with: string[];
  permissions: {
    can_view: boolean;
    can_customize_local: boolean;
    can_publish_global: boolean;
  };
  capabilities: DesignCapability[];
};

export type DesignLabDraft = {
  schema_version: 1;
  revision: number;
  density: DesignDensity;
  collection_mode: DesignCollectionMode;
  simulated_state: DesignState;
  reduce_motion: boolean;
  project_name: string;
  audience: string;
  review_notes: string;
};
