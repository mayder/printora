import React from "react";
import { accessibilityApi, AccessibilityConflictError } from "../../services/accessibilityApi";
import { applyAccessibilityPreferences } from "../../services/accessibilityDocument";
import type {
  AccessibilityCatalog,
  AccessibilityPreferences,
  AccessibilityPreferenceValues,
} from "../../types/accessibility";


export type AccessibilityRouteMode = "list" | "detail" | "edit";

export function useAccessibilityCenter() {
  const [catalog, setCatalog] = React.useState<AccessibilityCatalog | null>(null);
  const [preferences, setPreferences] = React.useState<AccessibilityPreferences | null>(null);
  const [draft, setDraft] = React.useState<AccessibilityPreferenceValues | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [saveStatus, setSaveStatus] = React.useState<"idle" | "saved" | "conflict">("idle");
  const [offline, setOffline] = React.useState(() => !window.navigator.onLine);
  const [route, setRoute] = React.useState(readAccessibilityRoute);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextCatalog, nextPreferences] = await Promise.all([
        accessibilityApi.catalog(),
        accessibilityApi.preferences(),
      ]);
      setCatalog(nextCatalog);
      setPreferences(nextPreferences);
      setDraft(preferenceValues(nextPreferences));
      applyAccessibilityPreferences(nextPreferences);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Falha ao carregar acessibilidade.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void load();
  }, [load]);

  React.useEffect(() => {
    const handleOnline = () => setOffline(false);
    const handleOffline = () => setOffline(true);
    const handlePopState = () => setRoute(readAccessibilityRoute());
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  function updateDraft(patch: Partial<AccessibilityPreferenceValues>) {
    if (!draft) return;
    const next = { ...draft, ...patch };
    setDraft(next);
    setSaveStatus("idle");
    applyAccessibilityPreferences(next);
  }

  async function save() {
    if (!draft || !preferences || offline) return;
    setSaving(true);
    setError(null);
    try {
      const saved = await accessibilityApi.save(draft, preferences.revision);
      setPreferences(saved);
      setDraft(preferenceValues(saved));
      setSaveStatus("saved");
      applyAccessibilityPreferences(saved);
    } catch (saveError) {
      if (saveError instanceof AccessibilityConflictError) {
        setSaveStatus("conflict");
      } else {
        setError(saveError instanceof Error ? saveError.message : "Falha ao sincronizar preferências.");
      }
    } finally {
      setSaving(false);
    }
  }

  function navigate(path: string, mode: AccessibilityRouteMode = "list") {
    const nextPath = mode === "list" ? path : `${path}/${mode}`;
    window.history.pushState(null, "", nextPath);
    setRoute(readAccessibilityRoute());
  }

  return {
    catalog,
    draft,
    error,
    load,
    loading,
    navigate,
    offline,
    preferences,
    route,
    save,
    saveStatus,
    saving,
    updateDraft,
  };
}
function preferenceValues(
  preferences: AccessibilityPreferences,
): AccessibilityPreferenceValues {
  const {
    contract_version: _contract,
    compatible_with: _compatible,
    revision: _revision,
    updated_at: _updated,
    ...values
  } = preferences;
  return values;
}

function readAccessibilityRoute(): { slug: string | null; mode: AccessibilityRouteMode } {
  const match = window.location.pathname.match(
    /^\/community\/accessibility\/([a-z0-9-]+)(?:\/(detail|edit))?\/?$/i,
  );
  return {
    slug: match?.[1] ?? null,
    mode: (match?.[2] as AccessibilityRouteMode | undefined) ?? "list",
  };
}
