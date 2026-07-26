export type AccessibilityState =
  | "loading"
  | "empty"
  | "error"
  | "success"
  | "partial"
  | "offline"
  | "forbidden"
  | "conflict";

export type AccessibilityTheme = "system" | "light" | "dark" | "high-contrast";
export type TactileFormat = "svg" | "brf";

export type AccessibilityCapability = {
  capability_id: string;
  com_ids: string[];
  screen_id: string;
  slug: string;
  title: string;
  summary: string;
  route: string;
  evidence: string[];
  supported_states: AccessibilityState[];
};

export type AccessibilityCatalog = {
  contract_version: string;
  compatible_with: string[];
  capabilities: AccessibilityCapability[];
};

export type AccessibilityPreferenceValues = {
  theme: AccessibilityTheme;
  text_scale_percent: number;
  reduce_motion: boolean;
  screen_reader_announcements: boolean;
  keyboard_navigation: boolean;
  voice_navigation: boolean;
  captions: boolean;
  audio_descriptions: boolean;
  simple_language: boolean;
  low_cognitive_load: boolean;
  three_d_text_alternative: boolean;
  tactile_format: TactileFormat;
};

export type AccessibilityPreferences = AccessibilityPreferenceValues & {
  contract_version: string;
  compatible_with: string[];
  revision: number;
  updated_at: string | null;
};

export function defaultAccessibilityValues(): AccessibilityPreferenceValues {
  return {
    theme: "system",
    text_scale_percent: 100,
    reduce_motion: false,
    screen_reader_announcements: true,
    keyboard_navigation: true,
    voice_navigation: false,
    captions: true,
    audio_descriptions: false,
    simple_language: false,
    low_cognitive_load: false,
    three_d_text_alternative: true,
    tactile_format: "svg",
  };
}
