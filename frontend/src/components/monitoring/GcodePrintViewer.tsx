import React from "react";
import { Home, RotateCcw, RotateCw, ZoomIn, ZoomOut } from "lucide-react";
import { operationApi } from "../../services/operationApi";
import { buildLayerOffsets, previewTargetPosition, sliceGcodeTextForPreview, type GcodePreviewMode } from "./gcodePreview";

type GCodeViewerInstance = InstanceType<
  (typeof import("@sindarius/gcodeviewer"))["default"]
>;

type BuildVolumeBounds = {
  min: [number, number, number];
  max: [number, number, number];
};

type CameraPreset = "iso" | "top" | "front" | "right" | "frontRight" | "frontLeft";

const MAINSAIL_EXTRUDER_COLORS = ["#E76F51", "#F4A261", "#E9C46A", "#2A9D8F", "#264653"] as const;
const MAX_RENDER_QUALITY_BYTES = 42 * 1024 * 1024;
const PREVIEW_EXPANSION_MARGIN_BYTES = 512 * 1024;

type ViewerVector = {
  x: number;
  y: number;
  z: number;
  copyFromFloats?: (x: number, y: number, z: number) => void;
};

type ViewerCamera = {
  name?: string;
  alpha?: number;
  beta?: number;
  radius?: number;
  position?: ViewerVector;
  target?: ViewerVector;
  viewport?: ViewerViewport;
};

type ViewerViewport = {
  x: number;
  y: number;
  width: number;
  height: number;
};

type ViewerSceneRuntime = {
  activeCamera?: ViewerCamera;
  cameras?: ViewerCamera[];
  meshes?: Array<{
    name?: string;
    material?: {
      name?: string;
      diffuseColor?: {
        r: number;
        g: number;
        b: number;
      };
    };
  }>;
  render?: (force?: boolean) => void;
};

type ViewerRuntime = GCodeViewerInstance & {
  canvas?: HTMLCanvasElement;
  engine?: {
    scenes?: ViewerSceneRuntime[];
  };
  orbitCamera?: ViewerCamera;
  scene?: ViewerSceneRuntime;
  displayViewBox?: (enabled: boolean) => void;
};

type ViewerProcessorRuntime = GCodeViewerInstance["gcodeProcessor"] & {
  renderAnimation?: boolean;
  setRenderAnimation?: (enabled: boolean) => void;
};

export function GcodePrintViewer({
  printerId,
  filename,
  mode = "progress",
  selectedLayer,
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
  mode?: GcodePreviewMode;
  selectedLayer?: number | null;
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
  const renderedSourceLimitRef = React.useRef(0);
  const renderBusyRef = React.useRef(false);
  const queuedRenderTargetRef = React.useRef<number | null>(null);
  const disposedRef = React.useRef(false);
  const liveRef = React.useRef({ filePosition, printState, progress, currentLayer, totalLayers, mode, selectedLayer });
  const boundsSignature = buildVolumeSignature(buildVolume);
  const bounds = React.useMemo(() => buildVolumeBounds(buildVolume), [boundsSignature]);
  const [state, setState] = React.useState<"idle" | "loading" | "ready" | "error">("idle");
  const [loadPercent, setLoadPercent] = React.useState(0);
  const [loadLabel, setLoadLabel] = React.useState("Renderizando G-code");
  const [error, setError] = React.useState("");
  const [panOffset, setPanOffset] = React.useState({ x: 0, y: 0 });

  React.useEffect(() => {
    liveRef.current = { filePosition, printState, progress, currentLayer, totalLayers, mode, selectedLayer };
  }, [currentLayer, filePosition, mode, printState, progress, selectedLayer, totalLayers]);

  React.useEffect(() => {
    let disposed = false;
    disposedRef.current = false;
    const abortController = new AbortController();
    const canvas = canvasRef.current;
    if (!canvas || !filename) return undefined;
    const canvasElement = canvas;

    async function loadViewer() {
      setState("loading");
      setLoadPercent(0);
      setLoadLabel("Preparando G-code");
      setError("");
      setPanOffset({ x: 0, y: 0 });
      const previous = viewerRef.current;
      if (previous) {
        previous.gcodeProcessor.loadingProgressCallback = null;
        previous.clearScene(true);
        viewerRef.current = null;
      }
      try {
        const [{ default: GCodeViewer }, text] = await Promise.all([
          import("@sindarius/gcodeviewer"),
          operationApi.gcodeCacheTextWithRecovery(printerId, filename, {
            signal: abortController.signal,
            onRetry: (attempt, maximum) => {
              if (!disposed) {
                setLoadLabel(`Recuperando preview automaticamente (${attempt}/${maximum})`);
                setLoadPercent(0);
              }
            },
          }),
        ]);
        if (disposed) return;
        const layerOffsets = buildLayerOffsets(text);
        const sourceFileSize = text.length;
        fullGcodeRef.current = text;
        fileSizeRef.current = sourceFileSize;
        layerOffsetsRef.current = layerOffsets;
        const viewer = new GCodeViewer(canvasElement);
        viewerRef.current = viewer;
        await viewer.init();
        const target = previewTargetPosition(
          sourceFileSize,
          layerOffsets,
          liveRef.current.mode,
          liveRef.current.selectedLayer,
          liveRef.current.filePosition,
          liveRef.current.printState,
          liveRef.current.progress,
          liveRef.current.currentLayer,
          liveRef.current.totalLayers,
        );
        await processSourceGcodePreview(viewer, target, { resetCamera: true, isDisposed: () => disposed || disposedRef.current });
      } catch (err) {
        if (disposed) return;
        setState("error");
        setError(err instanceof Error ? err.message : "Não foi possível carregar o G-code.");
      }
    }

    void loadViewer();
    return () => {
      disposed = true;
      disposedRef.current = true;
      abortController.abort();
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
      fileSizeRef.current = 0;
      layerOffsetsRef.current = [];
      renderedSourceLimitRef.current = 0;
    };
  }, [bounds, filename, nozzleDiameter, printerId]);

  React.useEffect(() => {
    const viewer = viewerRef.current;
    const fullGcode = fullGcodeRef.current;
    if (!viewer || !fileSizeRef.current || !fullGcode || state !== "ready") return;
    const target = previewTargetPosition(fileSizeRef.current, layerOffsetsRef.current, mode, selectedLayer, filePosition, printState, progress, currentLayer, totalLayers);
    if (renderedTargetRef.current === target) return;
    queuePreviewRender(target);
  }, [currentLayer, filePosition, mode, printState, progress, selectedLayer, state, totalLayers]);

  React.useEffect(() => {
    const viewer = viewerRef.current;
    const canvas = canvasRef.current;
    const container = canvas?.parentElement;
    if (!viewer || !container || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      viewer.resize();
      positionNativeViewbox(viewer);
      viewer.forceRender();
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, [state]);

  React.useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || typeof document === "undefined" || typeof MutationObserver === "undefined") return;
    const syncTheme = () => {
      applyViewerTheme(viewer);
      positionNativeViewbox(viewer);
      viewer.forceRender();
    };
    syncTheme();
    const observer = new MutationObserver((records) => {
      if (records.some((record) => record.attributeName === "data-theme")) syncTheme();
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
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
      void flushQueuedPreviewRender();
    });
  };

  async function flushQueuedPreviewRender() {
    const nextTarget = queuedRenderTargetRef.current;
    queuedRenderTargetRef.current = null;
    const viewer = viewerRef.current;
    try {
      if (viewer && nextTarget !== null) {
        if (needsRenderExpansion(nextTarget)) {
          await processSourceGcodePreview(viewer, nextTarget, { resetCamera: false, isDisposed: () => disposedRef.current || viewerRef.current !== viewer });
        } else {
          updatePreviewPosition(viewer, nextTarget);
          renderedTargetRef.current = nextTarget;
        }
      }
    } catch (err) {
      if (disposedRef.current) return;
      setState("error");
      setError(err instanceof Error ? err.message : "Não foi possível atualizar a prévia do G-code.");
    } finally {
      renderBusyRef.current = false;
      if (queuedRenderTargetRef.current !== null) {
        const pendingTarget = queuedRenderTargetRef.current;
        queuedRenderTargetRef.current = null;
        queuePreviewRender(pendingTarget);
      }
    }
  }

  async function processSourceGcodePreview(
    viewer: GCodeViewerInstance,
    sourceTarget: number,
    options: { resetCamera: boolean; isDisposed: () => boolean },
  ) {
    const sourceText = fullGcodeRef.current;
    if (!sourceText) return;
    const renderSlice = sliceGcodeTextForPreview(sourceText, sourceTarget);
    if (options.isDisposed()) return;
    setState("loading");
    setLoadPercent(0);
    setLoadLabel(renderSlice.partial ? "Renderizando trecho do G-code" : "Renderizando G-code");
    configureViewer(viewer, bounds, renderSlice.text.length, detectExtrusionWidth(sourceText, nozzleDiameter));
    viewer.gcodeProcessor.cancelLoad = false;
    viewer.gcodeProcessor.loadingProgressCallback = (value) => {
      if (!options.isDisposed()) setLoadPercent(Math.max(0, Math.min(100, Math.ceil(value * 100))));
    };
    await viewer.processFile(renderSlice.text);
    if (options.isDisposed()) return;
    viewer.gcodeProcessor.loadingProgressCallback = null;
    disablePreviewFade(viewer);
    applyViewerTheme(viewer);
    positionNativeViewbox(viewer);
    renderedSourceLimitRef.current = renderSlice.sourceLimit;
    const renderTarget = Math.min(sourceTarget, renderSlice.sourceLimit);
    updatePreviewPosition(viewer, renderTarget);
    renderedTargetRef.current = renderTarget;
    if (options.resetCamera) {
      setCameraPreset(viewer, "iso");
    }
    viewer.forceRender();
    setState("ready");
  }

  function needsRenderExpansion(sourceTarget: number) {
    const sourceFileSize = fileSizeRef.current;
    const renderedLimit = renderedSourceLimitRef.current;
    if (!sourceFileSize || !renderedLimit || renderedLimit >= sourceFileSize) return false;
    return sourceTarget >= renderedLimit - PREVIEW_EXPANSION_MARGIN_BYTES;
  }

  const layerText = viewerTitle(mode, selectedLayer, currentLayer, totalLayers);

  return (
    <div className={`gcode-viewer-tile${state === "error" ? " is-error" : ""}`}>
      <canvas ref={canvasRef} className="gcode-viewer-canvas" />
      <div className="gcode-viewer-title">
        <strong>{layerText}</strong>
      </div>
      {state === "loading" ? (
        <div className="gcode-viewer-status">
          <strong>{loadLabel}</strong>
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
      </div>
    </div>
  );
}

function configureViewer(viewer: GCodeViewerInstance, bounds: BuildVolumeBounds, fileBytes: number, extrusionWidth?: number | null) {
  applyViewerTheme(viewer);
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
  viewer.updateRenderQuality(fileBytes <= MAX_RENDER_QUALITY_BYTES ? 4 : 3);
  disablePreviewFade(viewer);
  showNativeViewbox(viewer, true);
}

function applyViewerTheme(viewer: GCodeViewerInstance) {
  const isLight = currentDocumentTheme() === "light";
  viewer.setBackgroundColor(isLight ? "#f4f9fc" : "#111820");
  viewer.bed.setBedColor(isLight ? "#d4e0ea" : "#334155");
}

function currentDocumentTheme() {
  if (typeof document === "undefined") return "dark";
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

function updatePreviewPosition(viewer: GCodeViewerInstance, target: number) {
  viewer.gcodeProcessor.updateFilePosition(target);
  viewer.forceRender();
}

function setCameraPreset(viewer: GCodeViewerInstance, preset: CameraPreset) {
  if (preset === "iso") {
    viewer.resetCamera();
    zoomCamera(viewer, 0.86);
    viewer.forceRender();
    return;
  }
  if (preset === "top" || preset === "front" || preset === "right") {
    viewer.resetCamera();
    const camera = cameraFromViewer(viewer);
    if (camera) {
      if (preset === "top") {
        camera.alpha = -Math.PI / 2;
        camera.beta = 0.08;
        zoomCamera(viewer, 0.74);
      }
      if (preset === "front") {
        camera.alpha = -Math.PI / 2;
        camera.beta = Math.PI / 2.45;
        zoomCamera(viewer, 0.86);
      }
      if (preset === "right") {
        camera.alpha = 0;
        camera.beta = Math.PI / 2.45;
        zoomCamera(viewer, 0.86);
      }
    }
    viewer.forceRender();
    return;
  }
  rotateCamera(viewer, preset === "frontLeft" ? -Math.PI / 2 : Math.PI / 2);
}

function disablePreviewFade(viewer: GCodeViewerInstance) {
  const processor = viewer.gcodeProcessor as ViewerProcessorRuntime;
  processor.renderAnimation = false;
  processor.setRenderAnimation?.(false);
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
  const forward =
    normalizeVector({
      x: camera.target.x - camera.position.x,
      y: camera.target.y - camera.position.y,
      z: camera.target.z - camera.position.z,
    }) ?? { x: 0, y: 0, z: -1 };
  const right = normalizeVector(crossVector(forward, { x: 0, y: 1, z: 0 })) ?? { x: 1, y: 0, z: 0 };
  const up = normalizeVector(crossVector(right, forward)) ?? { x: 0, y: 1, z: 0 };
  const move = {
    x: right.x * -deltaX + up.x * deltaY,
    y: right.y * -deltaX + up.y * deltaY,
    z: right.z * -deltaX + up.z * deltaY,
  };
  setVector(camera.target, camera.target.x + move.x, camera.target.y + move.y, camera.target.z + move.z);
  setVector(camera.position, camera.position.x + move.x, camera.position.y + move.y, camera.position.z + move.z);
  renderViewer(viewer);
}

function crossVector(left: ViewerVector, right: ViewerVector) {
  return {
    x: left.y * right.z - left.z * right.y,
    y: left.z * right.x - left.x * right.z,
    z: left.x * right.y - left.y * right.x,
  };
}

function normalizeVector(vector: ViewerVector) {
  const length = Math.hypot(vector.x, vector.y, vector.z);
  if (!Number.isFinite(length) || length < 0.0001) return null;
  return { x: vector.x / length, y: vector.y / length, z: vector.z / length };
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
  if (enabled) positionNativeViewbox(viewer);
}

function positionNativeViewbox(viewer: GCodeViewerInstance) {
  const runtime = viewer as ViewerRuntime;
  const viewboxScene = findNativeViewboxScene(runtime);
  if (!viewboxScene) return;
  const viewboxCamera = viewboxScene?.cameras?.find((camera) => camera.viewport);
  const viewport = viewboxCamera?.viewport;
  if (!viewport) return;
  const canvas = runtime.canvas;
  const canvasWidth = Math.max(1, canvas?.clientWidth ?? 0);
  const canvasHeight = Math.max(1, canvas?.clientHeight ?? 0);
  const side = Math.max(74, Math.min(112, Math.min(canvasWidth, canvasHeight) * 0.19));
  viewport.x = 14 / canvasWidth;
  viewport.y = 56 / canvasHeight;
  viewport.width = side / canvasWidth;
  viewport.height = side / canvasHeight;
  tintNativeViewbox(viewboxScene);
  viewboxScene.render?.(true);
}

function findNativeViewboxScene(runtime: ViewerRuntime) {
  const scenes = runtime.engine?.scenes ?? [];
  return (
    scenes.find((scene) => {
      const hasViewboxCamera = scene.cameras?.some((camera) => camera.name === "camera1" && camera.viewport);
      const hasViewboxMeshes = scene.meshes?.some((mesh) => mesh.name === "Top" || mesh.name === "Front" || mesh.name === "Right");
      return scene !== runtime.scene && Boolean(hasViewboxCamera && hasViewboxMeshes);
    }) ?? null
  );
}

function tintNativeViewbox(scene: ViewerSceneRuntime) {
  scene.meshes?.forEach((mesh) => {
    const material = mesh.material;
    if (material?.name !== "edgematerial" || !material.diffuseColor) return;
    material.diffuseColor.r = 0.18;
    material.diffuseColor.g = 0.33;
    material.diffuseColor.b = 0.38;
  });
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

function clampPan(value: number) {
  return Math.max(-180, Math.min(180, value));
}

function formatLayer(current: number, total?: number | null) {
  if (typeof total === "number" && Number.isFinite(total)) return `${current} / ${total}`;
  return `${current} / -`;
}

function viewerTitle(mode: GcodePreviewMode, selectedLayer?: number | null, currentLayer?: number | null, totalLayers?: number | null) {
  if (mode === "full") return "Arquivo completo";
  if (mode === "until_layer") return `Até camada ${formatLayer(selectedLayer ?? currentLayer ?? 0, totalLayers)}`;
  if (mode === "current_layer") return `Camada ${formatLayer(selectedLayer ?? currentLayer ?? 0, totalLayers)}`;
  if (typeof currentLayer === "number") return `Camada ${formatLayer(currentLayer, totalLayers)}`;
  return "Progresso";
}
