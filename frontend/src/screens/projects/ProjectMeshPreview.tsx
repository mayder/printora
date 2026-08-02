import React from "react";
import type { PrintProjectFile } from "../../types/printProjects";


export function ProjectMeshPreview({ file }: { file: PrintProjectFile }) {
  const triangles = file.inspection?.preview_triangles ?? [];
  const dimensions = file.inspection?.dimensions_mm;
  const [rotation, setRotation] = React.useState(35);
  const [section, setSection] = React.useState(100);
  const [scale, setScale] = React.useState(100);
  const drawing = React.useMemo(() => projectTriangles(triangles, rotation, section), [triangles, rotation, section]);

  if (!triangles.length || !dimensions) return null;
  return (
    <details className="project-mesh-preview">
      <summary>Ver forma em 3D</summary>
      <div className="project-mesh-canvas">
        <svg viewBox="0 0 320 220" role="img" aria-label={`Representação da malha de ${file.piece_name || file.file_name}`}>
          <rect x="0" y="0" width="320" height="220" rx="8" />
          {drawing.map((points, index) => <polygon key={`${points}-${index}`} points={points} />)}
        </svg>
      </div>
      <div className="project-mesh-controls">
        <label>Girar a peça<input type="range" min="0" max="360" value={rotation} onChange={(event) => setRotation(Number(event.target.value))} /></label>
        <label>Ver corte<input type="range" min="10" max="100" value={section} onChange={(event) => setSection(Number(event.target.value))} /></label>
        <label>Simular tamanho
          <select value={scale} onChange={(event) => setScale(Number(event.target.value))}>
            <option value="50">50%</option><option value="75">75%</option><option value="100">100%</option><option value="125">125%</option><option value="150">150%</option><option value="200">200%</option>
          </select>
        </label>
      </div>
      <p className="muted">No tamanho escolhido: {scaled(dimensions.x, scale)} × {scaled(dimensions.y, scale)} × {scaled(dimensions.z, scale)} mm. Esta simulação não altera o arquivo.</p>
    </details>
  );
}

function projectTriangles(triangles: number[][][], rotationDegrees: number, sectionPercent: number): string[] {
  const points = triangles.flat();
  if (!points.length) return [];
  const angle = rotationDegrees * Math.PI / 180;
  const rotated = points.map(([x, y, z]) => [x * Math.cos(angle) - y * Math.sin(angle), x * Math.sin(angle) + y * Math.cos(angle), z]);
  const maximumZ = Math.max(...rotated.map((point) => point[2]));
  const minimumZ = Math.min(...rotated.map((point) => point[2]));
  const sectionZ = minimumZ + (maximumZ - minimumZ) * sectionPercent / 100;
  const projected = rotated.map(([x, y, z]) => [x - y * 0.38, -z + y * 0.24, z]);
  const visible = projected.filter((point) => point[2] <= sectionZ + 1e-6);
  if (!visible.length) return [];
  const xs = visible.map((point) => point[0]);
  const ys = visible.map((point) => point[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const factor = Math.min(260 / Math.max(maxX - minX, 1), 170 / Math.max(maxY - minY, 1));
  let pointIndex = 0;
  return triangles.flatMap(() => {
    const triangle = projected.slice(pointIndex, pointIndex += 3);
    if (triangle.some((point) => point[2] > sectionZ + 1e-6)) return [];
    return [triangle.map((point) => `${55 + (point[0] - minX) * factor},${195 + (point[1] - maxY) * factor}`).join(" ")];
  });
}

function scaled(value: number, percent: number): string {
  return (value * percent / 100).toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}
