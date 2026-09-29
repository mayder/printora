import type { AccessibilityPreferenceValues } from "../types/accessibility";


export function applyAccessibilityPreferences(
  preferences: AccessibilityPreferenceValues,
  root: HTMLElement = document.documentElement,
): void {
  root.style.fontSize = `${preferences.text_scale_percent}%`;
  root.dataset.contrast = preferences.theme === "high-contrast" ? "high" : "standard";
  if (preferences.theme === "light" || preferences.theme === "dark") {
    root.dataset.theme = preferences.theme;
  }
  root.dataset.reduceMotion = preferences.reduce_motion ? "true" : "false";
  root.dataset.simpleLanguage = preferences.simple_language ? "true" : "false";
  root.dataset.lowCognitiveLoad = preferences.low_cognitive_load ? "true" : "false";
  root.dataset.captions = preferences.captions ? "true" : "false";
  root.dataset.audioDescriptions = preferences.audio_descriptions ? "true" : "false";
  root.dataset.screenReaderAnnouncements = preferences.screen_reader_announcements ? "true" : "false";
  root.dataset.keyboardNavigation = preferences.keyboard_navigation ? "true" : "false";
  root.dataset.voiceNavigation = preferences.voice_navigation ? "true" : "false";
}
