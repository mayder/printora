export type GcodePreviewMode = "progress" | "full" | "until_layer" | "current_layer";

const LIVE_TRACKING_OFFSET_BYTES = 350;
const LARGE_GCODE_MIN_RENDER_BYTES = 8 * 1024 * 1024;
const LARGE_GCODE_LOOKAHEAD_BYTES = 2 * 1024 * 1024;

export type GcodePreviewRenderSlice = {
  text: string;
  sourceLimit: number;
  sourceBytes: number;
  partial: boolean;
};

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
    : fileTargetPosition(fileSize, filePosition) ?? layerTargetPosition(layerOffsets, fileSize, currentLayer, totalLayers) ?? progressTargetPosition(fileSize, progress);
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

export function sliceGcodeTextForPreview(text: string, target: number): GcodePreviewRenderSlice {
  const sourceBytes = text.length;
  if (!sourceBytes) {
    return { text: "", sourceLimit: 0, sourceBytes: 0, partial: false };
  }
  const safeTarget = Math.max(0, Math.min(sourceBytes, Number.isFinite(target) ? target : 0));
  const desiredLimit = Math.min(sourceBytes, Math.max(LARGE_GCODE_MIN_RENDER_BYTES, safeTarget + LARGE_GCODE_LOOKAHEAD_BYTES));
  const sourceLimit = nextLineBoundary(text, desiredLimit);
  if (sourceLimit >= sourceBytes) {
    return { text, sourceLimit: sourceBytes, sourceBytes, partial: false };
  }
  return {
    text: text.slice(0, sourceLimit),
    sourceLimit,
    sourceBytes,
    partial: true,
  };
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

function nextLineBoundary(text: string, desiredLimit: number) {
  const safeLimit = Math.max(0, Math.min(text.length, Math.ceil(desiredLimit)));
  if (safeLimit >= text.length) return text.length;
  const nextNewline = text.indexOf("\n", safeLimit);
  return nextNewline === -1 ? text.length : nextNewline + 1;
}

function isLayerMarker(line: string, preferAfterLayerChange: boolean) {
  if (preferAfterLayerChange) return /^;AFTER_LAYER_CHANGE\b/i.test(line);
  return /^;LAYER:\s*\d+/i.test(line) || /^;LAYER_CHANGE\b/i.test(line);
}
