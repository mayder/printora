import React from "react";
import { Home, RotateCcw, RotateCw, ZoomIn, ZoomOut } from "lucide-react";
import type { OperationPrintScene, OperationPrintSceneSegment, OperationPrintVisual } from "../../types";

type Camera = {
  yaw: number;
  pitch: number;
  zoom: number;
};

type ProjectedPoint = {
  x: number;
  y: number;
};

type Drawing = {
  viewBox: string;
  gridPath: string;
  bedPath: string;
  futurePath: string;
  printedPath: string;
  currentPaths: Record<SceneLineType, string>;
  axis: Record<"x" | "y" | "z", { x1: number; y1: number; x2: number; y2: number }>;
};

const SCENE_LINE_TYPES = ["unknown", "outer-wall", "inner-wall", "sparse-infill", "solid-infill", "top-surface", "support", "skirt", "bridge"] as const;

type SceneLineType = (typeof SCENE_LINE_TYPES)[number];

const SCENE_LINE_TYPE_BY_CODE: Record<number, SceneLineType> = {
  1: "outer-wall",
  2: "inner-wall",
  3: "sparse-infill",
  4: "solid-infill",
  5: "top-surface",
  6: "support",
  7: "skirt",
  8: "bridge",
};

const EMPTY_LINE_PATHS = Object.fromEntries(SCENE_LINE_TYPES.map((type) => [type, ""])) as Record<SceneLineType, string>;

const CAMERA_PRESETS = {
  iso: { yaw: -42, pitch: 55, zoom: 1 },
  top: { yaw: 0, pitch: 90, zoom: 1 },
  front: { yaw: 0, pitch: 10, zoom: 1 },
  right: { yaw: 90, pitch: 10, zoom: 1 },
} satisfies Record<string, Camera>;

const EMPTY_DRAWING: Drawing = {
  viewBox: "-50 -50 100 100",
  gridPath: "",
  bedPath: "",
  futurePath: "",
  printedPath: "",
  currentPaths: EMPTY_LINE_PATHS,
  axis: {
    x: { x1: 0, y1: 0, x2: 18, y2: 0 },
    y: { x1: 0, y1: 0, x2: 0, y2: 18 },
    z: { x1: 0, y1: 0, x2: 0, y2: -18 },
  },
};

export function PrintVisual({ title, visual, emptyText }: { title: string; visual: OperationPrintVisual | null; emptyText: string }) {
  const [rotation, setRotation] = React.useState(0);
  const scene = visual?.scene?.kind === "gcode_layer_scene" ? visual.scene : null;
  const canRotateImage = visual?.source === "agent_gcode" && !scene;
  const layerText =
    typeof visual?.current_layer === "number"
      ? `Camada ${formatLayer(visual.current_layer, visual.total_layers ?? null)}`
      : "";

  const tileClass = ["print-visual-tile", scene ? "layer-scene-tile" : "", visual?.source === "moonraker_thumbnail" ? "thumbnail-tile" : ""].filter(Boolean).join(" ");

  return (
    <div className={tileClass}>
      <div className="print-visual-title">
        <strong>{title}</strong>
        {layerText ? <span>{layerText}</span> : null}
      </div>
      {scene ? (
        <LayerSceneViewer scene={scene} />
      ) : (
        <>
          {canRotateImage ? (
            <div className="print-visual-tools" aria-label="Rotação da imagem de camada">
              <button type="button" className="icon-button" title="Girar para a esquerda" aria-label="Girar imagem para a esquerda" onClick={() => setRotation((value) => value - 90)}>
                <RotateCcw size={13} />
              </button>
              <button type="button" className="icon-button" title="Girar para a direita" aria-label="Girar imagem para a direita" onClick={() => setRotation((value) => value + 90)}>
                <RotateCw size={13} />
              </button>
            </div>
          ) : null}
          {visual?.data_uri ? (
            <img className={canRotateImage ? "print-visual-image is-rotatable" : "print-visual-image"} src={visual.data_uri} alt="" loading="lazy" style={canRotateImage ? { transform: `rotate(${rotation}deg)` } : undefined} />
          ) : (
            <p>{emptyText}</p>
          )}
        </>
      )}
      {visual?.truncated || scene?.sampled ? <small className="print-visual-note">prévia parcial</small> : null}
    </div>
  );
}

function LayerSceneViewer({ scene }: { scene: OperationPrintScene }) {
  const [camera, setCamera] = React.useState<Camera>(CAMERA_PRESETS.iso);
  const pointerRef = React.useRef<{ x: number; y: number } | null>(null);
  const drawing = React.useMemo(() => buildDrawing(scene, camera), [scene, camera]);
  const isComplete = Boolean(scene.current_layer && scene.total_layers && scene.current_layer >= scene.total_layers);

  const setPreset = (preset: keyof typeof CAMERA_PRESETS) => setCamera(CAMERA_PRESETS[preset]);
  const zoomBy = (delta: number) => setCamera((value) => ({ ...value, zoom: clamp(value.zoom + delta, 0.65, 3.2) }));

  return (
    <div className={`layer-scene-viewer${isComplete ? " is-complete" : ""}`}>
      <svg
        viewBox={drawing.viewBox}
        role="img"
        aria-label={`Prévia do G-code até a camada ${scene.current_layer ?? "-"} de ${scene.total_layers ?? "-"}`}
        onPointerDown={(event) => {
          pointerRef.current = { x: event.clientX, y: event.clientY };
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (!pointerRef.current) return;
          const dx = event.clientX - pointerRef.current.x;
          const dy = event.clientY - pointerRef.current.y;
          pointerRef.current = { x: event.clientX, y: event.clientY };
          setCamera((value) => ({
            ...value,
            yaw: value.yaw + dx * 0.35,
            pitch: clamp(value.pitch - dy * 0.25, 10, 90),
          }));
        }}
        onPointerUp={(event) => {
          pointerRef.current = null;
          event.currentTarget.releasePointerCapture(event.pointerId);
        }}
        onPointerCancel={() => {
          pointerRef.current = null;
        }}
        onWheel={(event) => {
          event.preventDefault();
          zoomBy(event.deltaY > 0 ? -0.12 : 0.12);
        }}
      >
        <path className="layer-scene-grid" d={drawing.gridPath} />
        <path className="layer-scene-bed" d={drawing.bedPath} />
        <path className="layer-scene-future" d={drawing.futurePath} />
        <path className="layer-scene-printed" d={drawing.printedPath} />
        {SCENE_LINE_TYPES.map((type) =>
          drawing.currentPaths[type] ? <path key={type} className={`layer-scene-current ${type}`} d={drawing.currentPaths[type]} /> : null,
        )}
        <g className="layer-scene-axis">
          <line className="x" x1={drawing.axis.x.x1} y1={drawing.axis.x.y1} x2={drawing.axis.x.x2} y2={drawing.axis.x.y2} />
          <line className="y" x1={drawing.axis.y.x1} y1={drawing.axis.y.y1} x2={drawing.axis.y.x2} y2={drawing.axis.y.y2} />
          <line className="z" x1={drawing.axis.z.x1} y1={drawing.axis.z.y1} x2={drawing.axis.z.x2} y2={drawing.axis.z.y2} />
        </g>
      </svg>
      <div className="layer-scene-toolbar">
        <button type="button" className="icon-button" title="Girar para a esquerda" aria-label="Girar câmera para a esquerda" onClick={() => setCamera((value) => ({ ...value, yaw: value.yaw - 25 }))}>
          <RotateCcw size={14} />
        </button>
        <button type="button" className="icon-button" title="Girar para a direita" aria-label="Girar câmera para a direita" onClick={() => setCamera((value) => ({ ...value, yaw: value.yaw + 25 }))}>
          <RotateCw size={14} />
        </button>
        <button type="button" className="icon-button" title="Aproximar" aria-label="Aproximar prévia" onClick={() => zoomBy(0.18)}>
          <ZoomIn size={14} />
        </button>
        <button type="button" className="icon-button" title="Afastar" aria-label="Afastar prévia" onClick={() => zoomBy(-0.18)}>
          <ZoomOut size={14} />
        </button>
        <button type="button" className="icon-button" title="Vista inicial" aria-label="Restaurar vista isométrica" onClick={() => setPreset("iso")}>
          <Home size={14} />
        </button>
      </div>
      <div className="layer-scene-presets" aria-label="Vistas da prévia">
        <button type="button" onClick={() => setPreset("top")}>
          Top
        </button>
        <button type="button" onClick={() => setPreset("front")}>
          Front
        </button>
        <button type="button" onClick={() => setPreset("right")}>
          Right
        </button>
      </div>
      <div className="layer-nav-cube" aria-label="Navegador 3D">
        <button type="button" className="cube-face top" onClick={() => setPreset("top")}>
          Top
        </button>
        <button type="button" className="cube-face front" onClick={() => setPreset("front")}>
          Front
        </button>
        <button type="button" className="cube-face right" onClick={() => setPreset("right")}>
          Right
        </button>
        <span className="cube-axis x">X</span>
        <span className="cube-axis y">Y</span>
        <span className="cube-axis z">Z</span>
      </div>
    </div>
  );
}

function buildDrawing(scene: OperationPrintScene, camera: Camera): Drawing {
  const printed = normalizeSegments(scene.printed);
  const current = normalizeSegments(scene.current);
  const future = normalizeSegments(scene.future);
  const bed = expandBed(normalizeBed(scene.bed, [...printed, ...current]));
  const grid = gridSegments(bed);
  const center = { x: (bed[0] + bed[2]) / 2, y: (bed[1] + bed[3]) / 2 };
  const project = (x: number, y: number, z: number) => projectPoint(x - center.x, y - center.y, z, camera);
  const projectedSegments = [...grid, ...bedBorderSegments(bed), ...printed, ...current].flatMap((segment) => [project(segment[0], segment[1], segment[2]), project(segment[3], segment[4], segment[5])]);
  const bounds = drawingBounds(projectedSegments);
  const viewBox = zoomedViewBox(bounds, camera.zoom);

  return {
    viewBox,
    gridPath: pathForSegments(grid, project),
    bedPath: pathForSegments(bedBorderSegments(bed), project),
    futurePath: pathForSegments(future, project),
    printedPath: pathForSegments(printed, project),
    currentPaths: pathsByLineType(current, project),
    axis: axisLines(project, bed),
  };
}

function normalizeSegments(value: OperationPrintSceneSegment[] | null | undefined): OperationPrintSceneSegment[] {
  if (!Array.isArray(value)) return [];
  return value.filter((segment): segment is OperationPrintSceneSegment => Array.isArray(segment) && segment.length >= 6 && segment.every((item) => Number.isFinite(item)));
}

function normalizeBed(value: number[] | null | undefined, segments: OperationPrintSceneSegment[]): [number, number, number, number] {
  if (Array.isArray(value) && value.length >= 4 && value.slice(0, 4).every((item) => Number.isFinite(item))) {
    return [value[0], value[1], value[2], value[3]];
  }
  const xs = segments.flatMap((segment) => [segment[0], segment[3]]);
  const ys = segments.flatMap((segment) => [segment[1], segment[4]]);
  return [Math.min(...xs, 0), Math.min(...ys, 0), Math.max(...xs, 1), Math.max(...ys, 1)];
}

function expandBed(bed: [number, number, number, number]): [number, number, number, number] {
  const width = Math.max(1, bed[2] - bed[0]);
  const height = Math.max(1, bed[3] - bed[1]);
  const pad = Math.max(18, Math.max(width, height) * 0.18);
  return [bed[0] - pad, bed[1] - pad, bed[2] + pad, bed[3] + pad];
}

function gridSegments(bed: [number, number, number, number]): OperationPrintSceneSegment[] {
  const [minX, minY, maxX, maxY] = bed;
  const segments: OperationPrintSceneSegment[] = [];
  for (let index = 0; index <= 10; index += 1) {
    const x = minX + ((maxX - minX) * index) / 10;
    const y = minY + ((maxY - minY) * index) / 10;
    segments.push([x, minY, 0, x, maxY, 0], [minX, y, 0, maxX, y, 0]);
  }
  return segments;
}

function bedBorderSegments(bed: [number, number, number, number]): OperationPrintSceneSegment[] {
  const [minX, minY, maxX, maxY] = bed;
  return [
    [minX, minY, 0, maxX, minY, 0],
    [maxX, minY, 0, maxX, maxY, 0],
    [maxX, maxY, 0, minX, maxY, 0],
    [minX, maxY, 0, minX, minY, 0],
  ];
}

function projectPoint(x: number, y: number, z: number, camera: Camera): ProjectedPoint {
  const yaw = degreesToRadians(camera.yaw);
  const pitch = degreesToRadians(camera.pitch);
  return {
    x: x * Math.cos(yaw) - y * Math.sin(yaw),
    y: (x * Math.sin(yaw) + y * Math.cos(yaw)) * Math.sin(pitch) - z * Math.cos(pitch) * 2.2,
  };
}

function pathForSegments(segments: OperationPrintSceneSegment[], project: (x: number, y: number, z: number) => ProjectedPoint) {
  return segments
    .map((segment) => {
      const start = project(segment[0], segment[1], segment[2]);
      const end = project(segment[3], segment[4], segment[5]);
      return `M${formatCoord(start.x)} ${formatCoord(start.y)}L${formatCoord(end.x)} ${formatCoord(end.y)}`;
    })
    .join("");
}

function pathsByLineType(segments: OperationPrintSceneSegment[], project: (x: number, y: number, z: number) => ProjectedPoint) {
  const grouped = Object.fromEntries(SCENE_LINE_TYPES.map((type) => [type, [] as OperationPrintSceneSegment[]])) as Record<SceneLineType, OperationPrintSceneSegment[]>;
  segments.forEach((segment) => {
    grouped[lineTypeForSegment(segment)].push(segment);
  });
  return Object.fromEntries(SCENE_LINE_TYPES.map((type) => [type, pathForSegments(grouped[type], project)])) as Record<SceneLineType, string>;
}

function lineTypeForSegment(segment: OperationPrintSceneSegment): SceneLineType {
  const code = Math.round(segment[6] ?? 0);
  return SCENE_LINE_TYPE_BY_CODE[code] ?? "unknown";
}

function drawingBounds(points: ProjectedPoint[]) {
  if (!points.length) return { minX: -50, minY: -50, maxX: 50, maxY: 50 };
  return points.reduce(
    (bounds, point) => ({
      minX: Math.min(bounds.minX, point.x),
      minY: Math.min(bounds.minY, point.y),
      maxX: Math.max(bounds.maxX, point.x),
      maxY: Math.max(bounds.maxY, point.y),
    }),
    { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity },
  );
}

function zoomedViewBox(bounds: { minX: number; minY: number; maxX: number; maxY: number }, zoom: number) {
  const rawWidth = Math.max(20, bounds.maxX - bounds.minX);
  const rawHeight = Math.max(20, bounds.maxY - bounds.minY);
  const padding = Math.max(8, Math.max(rawWidth, rawHeight) * 0.08);
  const width = (rawWidth + padding * 2) / zoom;
  const height = (rawHeight + padding * 2) / zoom;
  const centerX = (bounds.minX + bounds.maxX) / 2;
  const centerY = (bounds.minY + bounds.maxY) / 2;
  return `${formatCoord(centerX - width / 2)} ${formatCoord(centerY - height / 2)} ${formatCoord(width)} ${formatCoord(height)}`;
}

function axisLines(project: (x: number, y: number, z: number) => ProjectedPoint, bed: [number, number, number, number]): Drawing["axis"] {
  const length = Math.max(18, Math.min(42, Math.max(bed[2] - bed[0], bed[3] - bed[1]) * 0.18));
  const origin = project(bed[0], bed[1], 0);
  const x = project(bed[0] + length, bed[1], 0);
  const y = project(bed[0], bed[1] + length, 0);
  const z = project(bed[0], bed[1], length * 0.45);
  return {
    x: { x1: origin.x, y1: origin.y, x2: x.x, y2: x.y },
    y: { x1: origin.x, y1: origin.y, x2: y.x, y2: y.y },
    z: { x1: origin.x, y1: origin.y, x2: z.x, y2: z.y },
  };
}

function formatLayer(current: number, total: number | null) {
  if (total && total > 0) return `${current} / ${total}`;
  return String(current);
}

function degreesToRadians(value: number) {
  return (value * Math.PI) / 180;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function formatCoord(value: number) {
  return Number.isFinite(value) ? value.toFixed(2) : "0";
}
