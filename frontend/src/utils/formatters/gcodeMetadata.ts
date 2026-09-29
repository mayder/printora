const EMPTY_METADATA_VALUES = new Set(["", "-", "?", "unknown", "unknown ?", "n/a", "null", "undefined"]);

function cleanMetadataValue(value?: string | null) {
  const clean = (value ?? "").trim();
  return EMPTY_METADATA_VALUES.has(clean.toLowerCase()) ? "" : clean;
}

export function normalizeGcodeMaterial(value?: string | null) {
  const clean = cleanMetadataValue(value);
  if (!clean) return "";

  let values: string[] = [];
  if (clean.startsWith("[") && clean.endsWith("]")) {
    try {
      const parsed = JSON.parse(clean);
      if (Array.isArray(parsed)) values = parsed.filter((item): item is string => typeof item === "string");
    } catch {
      values = [];
    }
  }
  if (values.length === 0) values = clean.split(";");

  const unique = new Map<string, string>();
  for (const valueItem of values) {
    const item = cleanMetadataValue(valueItem.replace(/^["']|["']$/g, ""));
    if (item) unique.set(item.toLocaleLowerCase("pt-BR"), item);
  }
  return [...unique.values()].join(" · ");
}

export function formatGcodeSlicer(slicer?: string | null, version?: string | null) {
  const cleanSlicer = cleanMetadataValue(slicer);
  if (!cleanSlicer) return "-";
  const cleanVersion = cleanMetadataValue(version);
  return [cleanSlicer, cleanVersion].filter(Boolean).join(" ");
}
