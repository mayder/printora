const OFFSET_SUFFIX = /(?:Z|[+-]\d{2}:?\d{2})$/i;

export function formatDateTime(value?: string | null) {
  const date = parsePrintoraDate(value);
  if (!date) {
    return value || "-";
  }
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(date);
}

function parsePrintoraDate(value?: string | null) {
  if (!value) {
    return null;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const normalized = OFFSET_SUFFIX.test(trimmed)
    ? trimmed
    : `${trimmed.replace(" ", "T")}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}
