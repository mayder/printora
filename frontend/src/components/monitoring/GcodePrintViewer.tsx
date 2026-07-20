import React from "react";
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, Home, RotateCcw, RotateCw, ZoomIn, ZoomOut } from "lucide-react";
import type GCodeViewerClass from "@sindarius/gcodeviewer";
import { operationApi } from "../../services/operationApi";

type GCodeViewerInstance = InstanceType<typeof GCodeViewerClass>;

type BuildVolumeBounds = {
  min: [number, number, number];
  max: [number, number, number];
};

type CameraPreset = "iso" | "frontRight" | "frontLeft";

const MAINSAIL_EXTRUDER_COLORS = ["#E76F51", "#F4A261", "#E9C46A", "#2A9D8F", "#264653"] as const;

export function GcodePrintViewer({
  printerId,
  filename,
  filePosition,
  currentLayer,
  totalLayers,
  printState,
  progress,
  buildVolume,
  nozzleDiameter,
}: {
  printerId: number;
  filename: string;
  filePosition?: number | null;
  currentLayer?: number | null;
  totalLayers?: number | null;
  printState?: string | null;
  progress?: number | null;
  buildVolume?: Record<string, unknown> | null;
  nozzleDiameter?: number | null;
}) {
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);
  const viewerRef = React.useRef<GCodeViewerInstance | null>(null);
  const fullGcodeRef = React.useRef("");
  const fileSizeRef = React.useRef(0);
  const layerOffsetsRef = React.useRef<number[]>([]);
  const renderedTargetRef = React.useRef<number | null>(null);
  const renderBusyRef = React.useRef(false);
  const queuedRenderTargetRef = React.useRef<number | null>(null);
  const liveRef = React.useRef({ filePosition, printState, progress, currentLayer, totalLayers });
  const bounds = React.useMemo(() => buildVolumeBounds(buildVolume), [buildVolume]);
  const [state, setState] = React.useState<"idle" | "loading" | "ready" | "error">("idle");
  const [loadPercent, setLoadPercent] = React.useState(0);
  const [error, setError] = React.useState("");
  const [panOffset, setPanOffset] = React.useState({ x: 0, y: 0 });

  React.useEffect(() => {
    liveRef.current = { filePosition, printState, progress, currentLayer, totalLayers };
  }, [currentLayer, filePosition, printState, progress, totalLayers]);

  React.useEffect(() => {
    let disposed = false;
    const canvas = canvasRef.current;
    if (!canvas || !filename) return undefined;
    const canvasElement = canvas;

    async function loadViewer() {
      setState("loading");
      setLoadPercent(0);
      setError("");
      setPanOffset({ x: 0, y: 0 });
      const previous = viewerRef.current;
      if (previous) {
        previous.gcodeProcessor.loadingProgressCallback = null;
        previous.clearScene(true);
        viewerRef.current = null;
      }
      try {
        const [{ default: GCodeViewer }, cache] = await Promise.all([
          import("@sindarius/gcodeviewer"),
          operationApi.ensureGcodeCache(printerId, filename),
        ]);
        const text = await operationApi.gcodeCacheText(printerId, cache.cache_key);
        if (disposed) return;
        const viewer = new GCodeViewer(canvasElement);
        viewerRef.current = viewer;
        await viewer.init();
        configureViewer(viewer, bounds, nozzleDiameter);
        viewer.gcodeProcessor.loadingProgressCallback = (value) => {
          if (!disposed) setLoadPercent(Math.max(0, Math.min(100, Math.ceil(value * 100))));
        };
        const layerOffsets = buildLayerOffsets(text);
        await viewer.processFile(text);
        const parsedFileSize = validFileSize(viewer.fileSize) ? viewer.fileSize : text.length;
        const target = previewTargetPosition(
          parsedFileSize,
          layerOffsets,
          liveRef.current.filePosition,
          liveRef.current.printState,
          liveRef.current.progress,
          liveRef.current.currentLayer,
          liveRef.current.totalLayers,
        );
        updatePreviewPosition(viewer, target);
        if (disposed) return;
        fullGcodeRef.current = text;
        fileSizeRef.current = parsedFileSize;
        layerOffsetsRef.current = layerOffsets;
        renderedTargetRef.current = target;
        setCameraPreset(viewer, bounds, "iso");
        viewer.forceRender();
        setState("ready");
      } catch (err) {
        if (disposed) return;
        setState("error");
        setError(err instanceof Error ? err.message : "Não foi possível carregar o G-code.");
      }
    }

    void loadViewer();
    return () => {
      disposed = true;
      const viewer = viewerRef.current;
      if (viewer) {
        viewer.gcodeProcessor.cancelLoad = true;
        viewer.gcodeProcessor.loadingProgressCallback = null;
        viewer.clearScene(true);
      }
      viewerRef.current = null;
      renderedTargetRef.current = null;
      renderBusyRef.current = false;
      queuedRenderTargetRef.current = null;
      fullGcodeRef.current = "";
      layerOffsetsRef.current = [];
    };
  }, [bounds, filename, nozzleDiameter, printerId]);

  React.useEffect(() => {
    const viewer = viewerRef.current;
    const fullGcode = fullGcodeRef.current;
    if (!viewer || !fileSizeRef.current || !fullGcode || state !== "ready") return;
    const target = previewTargetPosition(fileSizeRef.current, layerOffsetsRef.current, filePosition, printState, progress, currentLayer, totalLayers);
    if (renderedTargetRef.current === target) return;
    queuePreviewRender(target);
  }, [currentLayer, filePosition, printState, progress, state, totalLayers]);

  React.useEffect(() => {
    const viewer = viewerRef.current;
    const canvas = canvasRef.current;
    const container = canvas?.parentElement;
    if (!viewer || !container || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      viewer.resize();
      viewer.forceRender();
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, [state]);

  const setPreset = (preset: CameraPreset) => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    setPanOffset({ x: 0, y: 0 });
    setCameraPreset(viewer, bounds, preset);
  };

  const zoom = (scale: number) => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    const position = vectorLike(viewer.getCameraPosition());
    const target = vectorLike(viewer.getCameraTarget());
    if (!position || !target) return;
    viewer.setCameraPosition(
      target[0] + (position[0] - target[0]) * scale,
      target[1] + (position[1] - target[1]) * scale,
      target[2] + (position[2] - target[2]) * scale,
    );
  };

  const pan = (deltaX: number, deltaY: number) => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    const position = vectorLike(viewer.getCameraPosition());
    const target = vectorLike(viewer.getCameraTarget());
    if (!position || !target) return;
    viewer.setCameraTarget(target[0] + deltaX, target[1] + deltaY, target[2]);
    viewer.setCameraPosition(position[0] + deltaX, position[1] + deltaY, position[2]);
  };

  const panRelative = (deltaX: number, deltaY: number) => {
    pan(deltaX, deltaY);
    setPanOffset((current) => ({
      x: clampPan(current.x + deltaX),
      y: clampPan(current.y + deltaY),
    }));
  };

  const panTo = (axis: "x" | "y", rawValue: string) => {
    const value = Number(rawValue);
    if (!Number.isFinite(value)) return;
    const nextValue = clampPan(value);
    const currentValue = panOffset[axis];
    const delta = nextValue - currentValue;
    if (delta === 0) return;
    pan(axis === "x" ? delta : 0, axis === "y" ? delta : 0);
    setPanOffset((current) => ({ ...current, [axis]: nextValue }));
  };

  const queuePreviewRender = (target: number) => {
    queuedRenderTargetRef.current = target;
    if (renderBusyRef.current) return;
    renderBusyRef.current = true;
    window.requestAnimationFrame(() => {
      const nextTarget = queuedRenderTargetRef.current;
      queuedRenderTargetRef.current = null;
      const viewer = viewerRef.current;
      if (viewer && nextTarget !== null) {
        updatePreviewPosition(viewer, nextTarget);
        renderedTargetRef.current = nextTarget;
      }
      renderBusyRef.current = false;
    });
  };

  const layerText = typeof currentLayer === "number" ? `Camada ${formatLayer(currentLayer, totalLayers)}` : "Camada";

  return (
    <div className={`gcode-viewer-tile${state === "error" ? " is-error" : ""}`}>
      <canvas ref={canvasRef} className="gcode-viewer-canvas" />
      <div className="gcode-viewer-title">
        <strong>{layerText}</strong>
      </div>
      {state === "loading" ? (
        <div className="gcode-viewer-status">
          <strong>Renderizando G-code</strong>
          <span>{loadPercent}%</span>
        </div>
      ) : null}
      {state === "error" ? (
        <div className="gcode-viewer-status is-error">
          <strong>Preview 3D indisponível</strong>
          <span>{error}</span>
        </div>
      ) : null}
      <input
        className="gcode-viewer-pan-range gcode-viewer-pan-x"
        type="range"
        min="-180"
        max="180"
        step="5"
        value={panOffset.x}
        aria-label="Mover preview para esquerda ou direita"
        onChange={(event) => panTo("x", event.target.value)}
      />
      <input
        className="gcode-viewer-pan-range gcode-viewer-pan-y"
        type="range"
        min="-180"
        max="180"
        step="5"
        value={panOffset.y}
        aria-label="Mover preview para cima ou baixo"
        onChange={(event) => panTo("y", event.target.value)}
      />
      <div className="gcode-viewer-toolbar" aria-label="Controles do preview 3D">
        <button type="button" className="icon-button" title="Girar para a esquerda" aria-label="Girar para a esquerda" onClick={() => setPreset("frontLeft")}>
          <RotateCcw size={14} />
        </button>
        <button type="button" className="icon-button" title="Girar para a direita" aria-label="Girar para a direita" onClick={() => setPreset("frontRight")}>
          <RotateCw size={14} />
        </button>
        <button type="button" className="icon-button" title="Aproximar" aria-label="Aproximar" onClick={() => zoom(0.82)}>
          <ZoomIn size={14} />
        </button>
        <button type="button" className="icon-button" title="Afastar" aria-label="Afastar" onClick={() => zoom(1.18)}>
          <ZoomOut size={14} />
        </button>
        <button type="button" className="icon-button" title="Vista inicial" aria-label="Vista inicial" onClick={() => setPreset("iso")}>
          <Home size={14} />
        </button>
        <span className="gcode-viewer-toolbar-separator" aria-hidden="true" />
        <button type="button" className="icon-button" title="Mover para cima" aria-label="Mover preview para cima" onClick={() => panRelative(0, -22)}>
          <ArrowUp size={14} />
        </button>
        <button type="button" className="icon-button" title="Mover para a esquerda" aria-label="Mover preview para a esquerda" onClick={() => panRelative(-22, 0)}>
          <ArrowLeft size={14} />
        </button>
        <button type="button" className="icon-button" title="Mover para a direita" aria-label="Mover preview para a direita" onClick={() => panRelative(22, 0)}>
          <ArrowRight size={14} />
        </button>
        <button type="button" className="icon-button" title="Mover para baixo" aria-label="Mover preview para baixo" onClick={() => panRelative(0, 22)}>
          <ArrowDown size={14} />
        </button>
      </div>
    </div>
  );
}

function configureViewer(viewer: GCodeViewerInstance, bounds: BuildVolumeBounds, nozzleDiameter?: number | null) {
  viewer.setBackgroundColor("#111820");
  viewer.bed.setBedColor("#334155");
  viewer.setCursorVisiblity(false);
  viewer.setZClipPlane(1000000, -1000000);
  viewer.axes.show(true);
  viewer.bed.setDelta(false);
  viewer.bed.buildVolume.x.min = bounds.min[0];
  viewer.bed.buildVolume.y.min = bounds.min[1];
  viewer.bed.buildVolume.z.min = bounds.min[2];
  viewer.bed.buildVolume.x.max = bounds.max[0];
  viewer.bed.buildVolume.y.max = bounds.max[1];
  viewer.bed.buildVolume.z.max = bounds.max[2];
  viewer.gcodeProcessor.useHighQualityExtrusion(false);
  viewer.gcodeProcessor.updateForceWireMode(false);
  viewer.gcodeProcessor.setAlpha(false);
  viewer.gcodeProcessor.setVoxelMode(false);
  viewer.gcodeProcessor.useSpecularColor(false);
  viewer.gcodeProcessor.setLiveTracking(false);
  viewer.gcodeProcessor.setLiveTrackingShowSolid(false);
  const processorSettings = viewer.gcodeProcessor as unknown as {
    progressMode?: boolean;
    keepProgressColor?: boolean;
    perimeterOnly?: boolean;
  };
  processorSettings.progressMode = false;
  processorSettings.keepProgressColor = false;
  processorSettings.perimeterOnly = false;
  viewer.gcodeProcessor.setRenderAnimation(false);
  viewer.gcodeProcessor.setTransparencyValue(0);
  viewer.gcodeProcessor.g1AsExtrusion = false;
  viewer.gcodeProcessor.setColorMode(2);
  viewer.gcodeProcessor.resetTools();
  MAINSAIL_EXTRUDER_COLORS.forEach((color) => viewer.gcodeProcessor.addTool(color, validNozzleDiameter(nozzleDiameter)));
  viewer.setProgressColor("#ECECEC");
  viewer.toggleTravels(false);
  viewer.updateRenderQuality(4);
  viewer.displayViewBox(true);
}

function updatePreviewPosition(viewer: GCodeViewerInstance, target: number) {
  viewer.gcodeProcessor.updateFilePosition(target);
  viewer.gcodeProcessor.forceRedraw();
  viewer.forceRender();
}

function previewTargetPosition(
  fileSize: number,
  layerOffsets: number[],
  filePosition?: number | null,
  printState?: string | null,
  progress?: number | null,
  currentLayer?: number | null,
  totalLayers?: number | null,
) {
  const completed = ["complete", "cancelled", "error"].includes((printState ?? "").toLowerCase());
  return completed
    ? fileSize
    : fileTargetPosition(fileSize, filePosition) ?? layerTargetPosition(layerOffsets, fileSize, currentLayer, totalLayers) ?? progressTargetPosition(fileSize, progress);
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
  return Math.max(0, Math.min(fileSize, filePosition - 350));
}

function progressTargetPosition(fileSize: number, progress?: number | null) {
  if (typeof progress !== "number" || !Number.isFinite(progress)) return fileSize;
  return Math.max(0, Math.min(fileSize, fileSize * (progress / 100)));
}

function buildLayerOffsets(text: string) {
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

function isLayerMarker(line: string, preferAfterLayerChange: boolean) {
  if (preferAfterLayerChange) return /^;AFTER_LAYER_CHANGE\b/i.test(line);
  return /^;LAYER:\s*\d+/i.test(line) || /^;LAYER_CHANGE\b/i.test(line);
}

function setCameraPreset(viewer: GCodeViewerInstance, bounds: BuildVolumeBounds, preset: CameraPreset) {
  const center = [
    (bounds.min[0] + bounds.max[0]) / 2,
    (bounds.min[1] + bounds.max[1]) / 2,
    (bounds.min[2] + bounds.max[2]) / 2,
  ] as const;
  const size = Math.max(bounds.max[0] - bounds.min[0], bounds.max[1] - bounds.min[1], bounds.max[2] - bounds.min[2], 180);
  const distance = size * 1.75;
  const presets: Record<CameraPreset, [number, number, number]> = {
    iso: [center[0] + distance, center[1] - distance, center[2] + distance * 0.75],
    frontRight: [bounds.max[0] + distance, bounds.min[1] - distance, center[2] + distance * 0.65],
    frontLeft: [bounds.min[0] - distance, bounds.min[1] - distance, center[2] + distance * 0.65],
  };
  const position = presets[preset];
  const targetZ = Math.max(bounds.min[2], Math.min(center[2], 55));
  viewer.setCameraTarget(center[0], center[1], targetZ);
  viewer.setCameraPosition(position[0], position[1], position[2]);
  viewer.forceRender();
}

function buildVolumeBounds(toolhead?: Record<string, unknown> | null): BuildVolumeBounds {
  const min = vectorFromUnknown(toolhead?.axis_minimum) ?? [0, 0, 0];
  const max = vectorFromUnknown(toolhead?.axis_maximum) ?? [350, 350, 350];
  return {
    min: [min[0], min[1], Math.min(min[2], 0)],
    max: [Math.max(max[0], min[0] + 180), Math.max(max[1], min[1] + 180), Math.max(max[2], min[2] + 120)],
  };
}

function vectorFromUnknown(value: unknown): [number, number, number] | null {
  if (!Array.isArray(value) || value.length < 3) return null;
  const numbers = value.slice(0, 3).map((item) => Number(item));
  if (numbers.some((item) => !Number.isFinite(item))) return null;
  return [numbers[0], numbers[1], numbers[2]];
}

function vectorLike(value: unknown): [number, number, number] | null {
  if (!value || typeof value !== "object") return null;
  const object = value as { x?: unknown; y?: unknown; z?: unknown };
  const x = Number(object.x);
  const y = Number(object.y);
  const z = Number(object.z);
  if (![x, y, z].every(Number.isFinite)) return null;
  return [x, z, y];
}

function validNozzleDiameter(value?: number | null) {
  if (typeof value === "number" && Number.isFinite(value) && value > 0 && value <= 2) return value;
  return 0.4;
}

function validFileSize(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value > 0;
}

function clampPan(value: number) {
  return Math.max(-180, Math.min(180, value));
}

function formatLayer(current: number, total?: number | null) {
  if (typeof total === "number" && Number.isFinite(total)) return `${current} / ${total}`;
  return `${current} / -`;
}
