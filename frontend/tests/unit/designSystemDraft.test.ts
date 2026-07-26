import { describe, expect, it } from "vitest";
import {
  defaultDesignLabDraft,
  DESIGN_DRAFT_KEY,
  readDesignLabDraft,
  saveDesignLabDraft,
} from "../../src/services/designSystemDraft";


describe("design system draft", () => {
  it("saves idempotently without duplicating revisions", () => {
    const storage = window.localStorage;
    storage.clear();
    const input = { ...defaultDesignLabDraft(), project_name: "Peça comunitária" };

    const first = saveDesignLabDraft(storage, input, 0);
    const repeated = saveDesignLabDraft(storage, input, 0);

    expect(first.status).toBe("saved");
    expect(repeated.status).toBe("unchanged");
    expect(readDesignLabDraft(storage).revision).toBe(1);
  });

  it("detects concurrent revisions before overwriting", () => {
    const storage = window.localStorage;
    storage.clear();
    const base = defaultDesignLabDraft();
    saveDesignLabDraft(storage, { ...base, audience: "Oficina" }, 0);

    const result = saveDesignLabDraft(storage, { ...base, audience: "Leitura" }, 0);

    expect(result.status).toBe("conflict");
    if (result.status === "conflict") {
      expect(result.current.audience).toBe("Oficina");
    }
  });

  it("normalizes malformed, oversized and future local payloads", () => {
    const storage = window.localStorage;
    storage.clear();
    storage.setItem(
      DESIGN_DRAFT_KEY,
      JSON.stringify({
        schema_version: 99,
        revision: -10,
        density: "invalid",
        collection_mode: "invalid",
        simulated_state: "invalid",
        project_name: "x".repeat(200),
      }),
    );

    const normalized = readDesignLabDraft(storage);
    expect(normalized.schema_version).toBe(1);
    expect(normalized.revision).toBe(0);
    expect(normalized.density).toBe("administration");
    expect(normalized.project_name).toHaveLength(120);

    storage.setItem(DESIGN_DRAFT_KEY, "x".repeat(33 * 1024));
    expect(readDesignLabDraft(storage)).toEqual(defaultDesignLabDraft());
  });
});
