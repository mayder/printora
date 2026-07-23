const OFFSET_SUFFIX = /(?:Z|[+-]\d{2}:?\d{2})$/i;
const SHORT_OFFSET_SUFFIX = /([+-]\d{2})$/;
const TIMEZONE_KEY = "printora.userTimezone";

let currentUserTimezone = readStoredTimezone();

export function formatDateTime(value?: string | null) {
  const date = parsePrintoraDate(value);
  if (!date) {
    return value || "-";
  }
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "medium",
    timeZone: currentUserTimezone,
  }).format(date);
}

export function formatTime(value: Date = new Date()) {
  return new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: currentUserTimezone,
  }).format(value);
}

export function setPrintoraUserTimezone(timezone?: string | null) {
  currentUserTimezone = normalizeTimezone(timezone);
  if (typeof window !== "undefined") {
    window.localStorage.setItem(TIMEZONE_KEY, currentUserTimezone);
  }
}

export function getPrintoraUserTimezone() {
  return currentUserTimezone;
}

export function browserTimezone() {
  return normalizeTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone);
}

export function parsePrintoraDate(value?: string | null) {
  if (!value) {
    return null;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const isoValue = trimmed.replace(" ", "T");
  const normalized = SHORT_OFFSET_SUFFIX.test(isoValue)
    ? isoValue.replace(SHORT_OFFSET_SUFFIX, "$1:00")
    : OFFSET_SUFFIX.test(isoValue)
      ? isoValue
      : `${isoValue}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

function readStoredTimezone() {
  if (typeof window === "undefined") {
    return browserTimezone();
  }
  return normalizeTimezone(window.localStorage.getItem(TIMEZONE_KEY) || browserTimezone());
}

function normalizeTimezone(value?: string | null) {
  const timezone = value?.trim() || "America/Sao_Paulo";
  try {
    new Intl.DateTimeFormat("pt-BR", { timeZone: timezone }).format(new Date());
    return timezone;
  } catch {
    return "America/Sao_Paulo";
  }
}
