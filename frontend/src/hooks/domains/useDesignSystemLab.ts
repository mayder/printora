import React from "react";
import { designSystemApi } from "../../services/designSystemApi";
import {
  defaultDesignLabDraft,
  DESIGN_DRAFT_KEY,
  readDesignLabDraft,
  saveDesignLabDraft,
} from "../../services/designSystemDraft";
import type { DesignLabDraft, DesignSystemCatalog } from "../../types/designSystem";


export type DesignRouteMode = "list" | "detail" | "edit";

export function useDesignSystemLab() {
  const [catalog, setCatalog] = React.useState<DesignSystemCatalog | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [offline, setOffline] = React.useState(() => !window.navigator.onLine);
  const [draft, setDraft] = React.useState(() => readDesignLabDraft(window.localStorage));
  const [saveStatus, setSaveStatus] = React.useState<"idle" | "saved" | "unchanged" | "conflict">("idle");
  const [route, setRoute] = React.useState(() => readDesignRoute());

  const loadCatalog = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setCatalog(await designSystemApi.catalog());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Falha ao carregar o design system.");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  React.useEffect(() => {
    const handleOnline = () => setOffline(false);
    const handleOffline = () => setOffline(true);
    const handlePopState = () => setRoute(readDesignRoute());
    const handleStorage = (event: StorageEvent) => {
      if (event.key !== DESIGN_DRAFT_KEY) return;
      const current = readDesignLabDraft(window.localStorage);
      if (current.revision !== draft.revision) {
        setSaveStatus("conflict");
      }
    };
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    window.addEventListener("popstate", handlePopState);
    window.addEventListener("storage", handleStorage);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("popstate", handlePopState);
      window.removeEventListener("storage", handleStorage);
    };
  }, [draft.revision]);

  React.useEffect(() => {
    document.documentElement.dataset.density = draft.density;
    document.documentElement.dataset.reduceMotion = draft.reduce_motion ? "true" : "false";
  }, [draft.density, draft.reduce_motion]);

  function updateDraft(patch: Partial<DesignLabDraft>) {
    setSaveStatus("idle");
    setDraft((current) => ({ ...current, ...patch }));
  }

  function saveDraft() {
    const result = saveDesignLabDraft(window.localStorage, draft, draft.revision);
    if (result.status === "conflict") {
      setSaveStatus("conflict");
      return;
    }
    setDraft(result.draft);
    setSaveStatus(result.status);
  }

  function loadCurrentDraft() {
    setDraft(readDesignLabDraft(window.localStorage));
    setSaveStatus("idle");
  }

  function restoreDefaults() {
    const result = saveDesignLabDraft(
      window.localStorage,
      { ...defaultDesignLabDraft(), revision: draft.revision },
      draft.revision,
    );
    if (result.status === "conflict") {
      setSaveStatus("conflict");
      return;
    }
    setDraft(result.draft);
    setSaveStatus("saved");
  }

  function navigate(path: string, mode: DesignRouteMode = "list") {
    const nextPath = mode === "list" ? path : `${path}/${mode}`;
    window.history.pushState(null, "", nextPath);
    setRoute(readDesignRoute());
  }

  return {
    catalog,
    draft,
    error,
    loadCatalog,
    loadCurrentDraft,
    loading,
    navigate,
    offline,
    restoreDefaults,
    route,
    saveDraft,
    saveStatus,
    updateDraft,
  };
}

function readDesignRoute(): { slug: string | null; mode: DesignRouteMode } {
  const match = window.location.pathname.match(
    /^\/community\/design_system\/([a-z0-9-]+)(?:\/(detail|edit))?\/?$/i,
  );
  return {
    slug: match?.[1] ?? null,
    mode: (match?.[2] as DesignRouteMode | undefined) ?? "list",
  };
}
