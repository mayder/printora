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
const MAX_RENDER_QUALITY_BYTES = 42 * 1024 * 1024;
const LIVE_TRACKING_OFFSET_BYTES = 350;

type ViewerVector = {
  x: number;
  y: number;
  z: number;
  copyFromFloats?: (x: number, y: number, z: number) => void;
};

type ViewerCamera = {
  alpha?: number;
  radius?: number;
  position?: ViewerVector;
  target?: ViewerVector;
};

type ViewerRuntime = GCodeViewerInstance & {
  orbitCamera?: ViewerCamera;
  scene?: {
    activeCamera?: ViewerCamera;
    render?: () => void;
  };
  displayViewBox?: (enabled: boolean) => void;
};

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
  const boundsSignature = buildVolumeSignature(buildVolume);
  const bounds = React.useMemo(() => buildVolumeBounds(buildVolume), [boundsSignature]);
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
        configureViewer(viewer, bounds, text.length, detectExtrusionWidth(text, nozzleDiameter));
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
        setCameraPreset(viewer, "iso");
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
    setCameraPreset(viewer, preset);
  };

  const zoom = (scale: number) => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    zoomCamera(viewer, scale);
  };

  const pan = (deltaX: number, deltaY: number) => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    panCamera(viewer, deltaX, deltaY);
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

function configureViewer(viewer: GCodeViewerInstance, bounds: BuildVolumeBounds, fileBytes: number, extrusionWidth?: number | null) {
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
  const processorSettings = viewer.gcodeProcessor as unknown as {
    progressMode?: boolean;
    keepProgressColor?: boolean;
    perimeterOnly?: boolean;
  };
  processorSettings.progressMode = false;
  processorSettings.keepProgressColor = false;
  processorSettings.perimeterOnly = false;
  viewer.gcodeProcessor.g1AsExtrusion = false;
  viewer.gcodeProcessor.setColorMode(2);
  viewer.gcodeProcessor.resetTools();
  MAINSAIL_EXTRUDER_COLORS.forEach((color) => viewer.gcodeProcessor.addTool(color, validExtrusionWidth(extrusionWidth)));
  viewer.setProgressColor("#ECECEC");
  viewer.toggleTravels(false);
  viewer.updateRenderQuality(fileBytes <= MAX_RENDER_QUALITY_BYTES ? 6 : 5);
  showNativeViewbox(viewer, true);
}

function updatePreviewPosition(viewer: GCodeViewerInstance, target: number) {
  viewer.gcodeProcessor.updateFilePosition(target);
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
  return Math.max(0, Math.min(fileSize, filePosition - LIVE_TRACKING_OFFSET_BYTES));
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

function setCameraPreset(viewer: GCodeViewerInstance, preset: CameraPreset) {
  if (preset === "iso") {
    viewer.resetCamera();
    viewer.forceRender();
    return;
  }
  rotateCamera(viewer, preset === "frontLeft" ? -Math.PI / 2 : Math.PI / 2);
}

function buildVolumeBounds(toolhead?: Record<string, unknown> | null): BuildVolumeBounds {
  const min = vectorFromUnknown(toolhead?.axis_minimum) ?? [0, 0, 0];
  const max = vectorFromUnknown(toolhead?.axis_maximum) ?? [350, 350, 350];
  return {
    min: [min[0], min[1], Math.min(min[2], 0)],
    max: [Math.max(max[0], min[0] + 180), Math.max(max[1], min[1] + 180), Math.max(max[2], min[2] + 120)],
  };
}

function buildVolumeSignature(toolhead?: Record<string, unknown> | null) {
  const bounds = buildVolumeBounds(toolhead);
  return `${bounds.min.join(":")}|${bounds.max.join(":")}`;
}

function vectorFromUnknown(value: unknown): [number, number, number] | null {
  if (!Array.isArray(value) || value.length < 3) return null;
  const numbers = value.slice(0, 3).map((item) => Number(item));
  if (numbers.some((item) => !Number.isFinite(item))) return null;
  return [numbers[0], numbers[1], numbers[2]];
}

function cameraFromViewer(viewer: GCodeViewerInstance): ViewerCamera | null {
  const runtime = viewer as ViewerRuntime;
  return runtime.orbitCamera ?? runtime.scene?.activeCamera ?? null;
}

function rotateCamera(viewer: GCodeViewerInstance, radians: number) {
  const camera = cameraFromViewer(viewer);
  if (!camera || typeof camera.alpha !== "number") {
    viewer.resetCamera();
    viewer.forceRender();
    return;
  }
  camera.alpha += radians;
  renderViewer(viewer);
}

function zoomCamera(viewer: GCodeViewerInstance, scale: number) {
  const camera = cameraFromViewer(viewer);
  if (!camera) return;
  if (typeof camera.radius === "number" && Number.isFinite(camera.radius)) {
    camera.radius = Math.max(24, Math.min(2400, camera.radius * scale));
    renderViewer(viewer);
    return;
  }
  if (!camera.position || !camera.target) return;
  const next = {
    x: camera.target.x + (camera.position.x - camera.target.x) * scale,
    y: camera.target.y + (camera.position.y - camera.target.y) * scale,
    z: camera.target.z + (camera.position.z - camera.target.z) * scale,
  };
  setVector(camera.position, next.x, next.y, next.z);
  renderViewer(viewer);
}

function panCamera(viewer: GCodeViewerInstance, deltaX: number, deltaY: number) {
  const camera = cameraFromViewer(viewer);
  if (!camera?.position || !camera.target) return;
  setVector(camera.target, camera.target.x + deltaX, camera.target.y, camera.target.z + deltaY);
  setVector(camera.position, camera.position.x + deltaX, camera.position.y, camera.position.z + deltaY);
  renderViewer(viewer);
}

function setVector(vector: ViewerVector, x: number, y: number, z: number) {
  if (typeof vector.copyFromFloats === "function") {
    vector.copyFromFloats(x, y, z);
    return;
  }
  vector.x = x;
  vector.y = y;
  vector.z = z;
}

function renderViewer(viewer: GCodeViewerInstance) {
  const runtime = viewer as ViewerRuntime;
  runtime.scene?.render?.();
  viewer.forceRender();
}

function showNativeViewbox(viewer: GCodeViewerInstance, enabled: boolean) {
  const runtime = viewer as ViewerRuntime;
  runtime.displayViewBox?.(enabled);
}

function detectExtrusionWidth(text: string, nozzleDiameter?: number | null) {
  const detectedNozzle = firstSlicerSettingNumber(text, ["nozzle_diameter", "nozzle_diameter_mm"]);
  const fallback = validExtrusionWidth(preferredNozzleWidth(nozzleDiameter ?? detectedNozzle));
  const widths = slicerSettingNumbers(text, [
    "line_width",
    "wall_line_width",
    "outer_wall_line_width",
    "inner_wall_line_width",
    "perimeter_extrusion_width",
    "external_perimeter_extrusion_width",
    "infill_extrusion_width",
    "sparse_infill_line_width",
    "solid_infill_extrusion_width",
    "internal_solid_infill_line_width",
    "top_infill_extrusion_width",
    "top_surface_line_width",
    "first_layer_extrusion_width",
    "first_layer_line_width",
    "support_material_extrusion_width",
    "support_line_width",
    "skirt_brim_line_width",
  ]).filter((value) => value >= 0.2 && value <= 2);
  if (!widths.length) return fallback;
  const sorted = [...widths].sort((left, right) => left - right);
  const representative = sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * 0.75))];
  return validExtrusionWidth(Math.max(fallback, representative));
}

function preferredNozzleWidth(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0 || value > 2) return null;
  return Math.min(2, value * 1.08);
}

function firstSlicerSettingNumber(text: string, keys: string[]) {
  return slicerSettingNumbers(text, keys)[0] ?? null;
}

function slicerSettingNumbers(text: string, keys: string[]) {
  const sample = text.length <= 440_000 ? text : `${text.slice(0, 220_000)}\n${text.slice(-220_000)}`;
  const values: number[] = [];
  keys.forEach((key) => {
    const expression = new RegExp(`^;\\s*${escapeRegExp(key)}\\s*=\\s*([^\\r\\n]+)`, "gim");
    let match: RegExpExecArray | null;
    while ((match = expression.exec(sample)) !== null) {
      const rawValue = match[1].split(";")[0];
      const numbers = rawValue.match(/[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)/g) ?? [];
      numbers.forEach((numberText) => {
        const value = Number(numberText.replace(",", "."));
        if (Number.isFinite(value)) values.push(value);
      });
    }
  });
  return values;
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function validExtrusionWidth(value?: number | null) {
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
