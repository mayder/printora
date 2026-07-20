export type GcodePreviewMode = "progress" | "full" | "until_layer" | "current_layer";

const LIVE_TRACKING_OFFSET_BYTES = 350;

export function previewTargetPosition(
  fileSize: number,
  layerOffsets: number[],
  mode: GcodePreviewMode,
  selectedLayer?: number | null,
  filePosition?: number | null,
  printState?: string | null,
  progress?: number | null,
  currentLayer?: number | null,
  totalLayers?: number | null,
) {
  if (mode === "full") return fileSize;
  if (mode === "until_layer" || mode === "current_layer") {
    return layerTargetPosition(layerOffsets, fileSize, selectedLayer ?? currentLayer, totalLayers) ?? fileSize;
  }
  const completed = ["complete", "cancelled", "error"].includes((printState ?? "").toLowerCase());
  return completed
    ? fileSize
    : layerTargetPosition(layerOffsets, fileSize, currentLayer, totalLayers) ?? fileTargetPosition(fileSize, filePosition) ?? progressTargetPosition(fileSize, progress);
}

export function buildLayerOffsets(text: string) {
  const offsets = [0];
  const preferAfterLayerChange = /^;AFTER_LAYER_CHANGE\b/im.test(text);
  let lineStart = 0;
  while (lineStart < text.length) {
    const lineEnd = text.indexOf("\n", lineStart);
    const nextStart = lineEnd === -1 ? text.length : lineEnd + 1;
    const rawLine = text.slice(lineStart, lineEnd === -1 ? text.length : lineEnd).trim();
    if (isLayerMarker(rawLine, preferAfterLayerChange) && lineStart - offsets[offsets.length - 1] > 64) {
      offsets.push(lineStart);
    }
    lineStart = nextStart;
  }
  if (offsets[offsets.length - 1] !== text.length) offsets.push(text.length);
  return offsets;
}

function layerTargetPosition(layerOffsets: number[], fileSize: number, currentLayer?: number | null, totalLayers?: number | null) {
  if (!Array.isArray(layerOffsets) || layerOffsets.length < 3) return null;
  if (typeof currentLayer !== "number" || !Number.isFinite(currentLayer) || currentLayer <= 0) return null;
  if (typeof totalLayers === "number" && Number.isFinite(totalLayers) && currentLayer >= totalLayers) return fileSize;
  const index = Math.max(1, Math.min(layerOffsets.length - 1, Math.floor(currentLayer) + 1));
  return Math.max(0, Math.min(fileSize, layerOffsets[index] ?? fileSize));
}

function fileTargetPosition(fileSize: number, filePosition?: number | null) {
  if (typeof filePosition !== "number" || !Number.isFinite(filePosition)) return null;
  return Math.max(0, Math.min(fileSize, filePosition - LIVE_TRACKING_OFFSET_BYTES));
}

function progressTargetPosition(fileSize: number, progress?: number | null) {
  if (typeof progress !== "number" || !Number.isFinite(progress)) return 0;
  const ratio = progress <= 1 ? progress : progress / 100;
  return Math.max(0, Math.min(fileSize, fileSize * ratio));
}

function isLayerMarker(line: string, preferAfterLayerChange: boolean) {
  if (preferAfterLayerChange) return /^;AFTER_LAYER_CHANGE\b/i.test(line);
  return /^;LAYER:\s*\d+/i.test(line) || /^;LAYER_CHANGE\b/i.test(line);
}
