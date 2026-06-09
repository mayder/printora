import { formatDateTime } from "./dates";

export function formatOptionalLocalDateTime(value?: string | null) {
  return value ? formatLocalDateTime(value) : "nunca";
}

export function formatLocalDateTime(value: string | Date) {
  return formatDateTime(value instanceof Date ? value.toISOString() : value);
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
