import type {
  DesignCollectionMode,
  DesignDensity,
  DesignLabDraft,
  DesignState,
} from "../types/designSystem";


export const DESIGN_DRAFT_KEY = "printora.design-system.lab.v1";
export const DESIGN_DRAFT_MAX_BYTES = 32 * 1024;

const DENSITIES: DesignDensity[] = ["workshop", "reading", "administration"];
const COLLECTION_MODES: DesignCollectionMode[] = ["cards", "table", "gallery"];
const DESIGN_STATES: DesignState[] = [
  "loading",
  "empty",
  "error",
  "success",
  "partial",
  "offline",
  "forbidden",
  "conflict",
];

export type DraftSaveResult =
  | { status: "saved" | "unchanged"; draft: DesignLabDraft }
  | { status: "conflict"; current: DesignLabDraft };

export function defaultDesignLabDraft(): DesignLabDraft {
  return {
    schema_version: 1,
    revision: 0,
    density: "administration",
    collection_mode: "cards",
    simulated_state: "success",
    reduce_motion: false,
    project_name: "",
    audience: "",
    review_notes: "",
  };
}

export function readDesignLabDraft(storage: Storage): DesignLabDraft {
  const raw = storage.getItem(DESIGN_DRAFT_KEY);
  if (!raw || byteLength(raw) > DESIGN_DRAFT_MAX_BYTES) {
    return defaultDesignLabDraft();
  }
  try {
    return normalizeDraft(JSON.parse(raw));
  } catch {
    return defaultDesignLabDraft();
  }
}

export function saveDesignLabDraft(
  storage: Storage,
  input: DesignLabDraft,
  expectedRevision: number,
): DraftSaveResult {
  const current = readDesignLabDraft(storage);
  const normalized = normalizeDraft(input);
  if (sameContent(current, normalized)) {
    return { status: "unchanged", draft: current };
  }
  if (current.revision !== expectedRevision) {
    return { status: "conflict", current };
  }
  const saved = { ...normalized, revision: expectedRevision + 1 } satisfies DesignLabDraft;
  const serialized = JSON.stringify(saved);
  if (byteLength(serialized) > DESIGN_DRAFT_MAX_BYTES) {
    throw new Error("Rascunho excede o limite local de 32 KiB.");
  }
  storage.setItem(DESIGN_DRAFT_KEY, serialized);
  return { status: "saved", draft: saved };
}

function normalizeDraft(value: unknown): DesignLabDraft {
  const source = isRecord(value) ? value : {};
  return {
    schema_version: 1,
    revision: boundedInteger(source.revision, 0, Number.MAX_SAFE_INTEGER),
    density: enumValue(source.density, DENSITIES, "administration"),
    collection_mode: enumValue(source.collection_mode, COLLECTION_MODES, "cards"),
    simulated_state: enumValue(source.simulated_state, DESIGN_STATES, "success"),
    reduce_motion: source.reduce_motion === true,
    project_name: boundedText(source.project_name, 120),
    audience: boundedText(source.audience, 240),
    review_notes: boundedText(source.review_notes, 2_000),
  };
}

function sameContent(left: DesignLabDraft, right: DesignLabDraft): boolean {
  return JSON.stringify({ ...left, revision: 0 }) === JSON.stringify({ ...right, revision: 0 });
}

function enumValue<T extends string>(value: unknown, allowed: T[], fallback: T): T {
  return typeof value === "string" && allowed.includes(value as T) ? (value as T) : fallback;
}

function boundedText(value: unknown, maxLength: number): string {
  return typeof value === "string" ? value.slice(0, maxLength) : "";
}

function boundedInteger(value: unknown, minimum: number, maximum: number): number {
  return typeof value === "number" && Number.isSafeInteger(value)
    ? Math.min(maximum, Math.max(minimum, value))
    : minimum;
}

function byteLength(value: string): number {
  return new TextEncoder().encode(value).byteLength;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
