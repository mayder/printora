export function formatOptionalLocalDateTime(value?: string | null) {
  return value ? formatLocalDateTime(value) : "nunca";
}

export function formatLocalDateTime(value: string | Date) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return typeof value === "string" ? value : "-";
  }
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

export function formatOptionalNumber(value: number | null | undefined) {
  return typeof value === "number" ? value.toFixed(3) : "-";
}

export function formatOptionalInt(value: number | null | undefined) {
  return typeof value === "number" ? String(value) : "-";
}

export function formatBoolean(value: boolean | null | undefined) {
  if (typeof value !== "boolean") {
    return "-";
  }
  return value ? "sim" : "não";
}
