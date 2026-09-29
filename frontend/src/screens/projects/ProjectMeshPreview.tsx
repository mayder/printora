import React from "react";
import type { PrintProjectFile } from "../../types/printProjects";
import { projectTriangles } from "./MeshShapeCanvas";


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

function scaled(value: number, percent: number): string {
  return (value * percent / 100).toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}
