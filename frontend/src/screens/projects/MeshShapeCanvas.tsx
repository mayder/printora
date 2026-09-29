import * as React from "react";


interface Props {
  triangles: number[][][];
  label: string;
}

export function MeshShapeCanvas({ triangles, label }: Props) {
  const drawing = React.useMemo(() => projectTriangles(triangles, 35), [triangles]);
  if (!drawing.length) return <p className="muted">Prévia indisponível para esta versão.</p>;
  return <div className="project-mesh-canvas">
    <svg viewBox="0 0 320 220" role="img" aria-label={label}>
      <rect x="0" y="0" width="320" height="220" rx="8" />
      {drawing.map((points, index) => <polygon key={`${points}-${index}`} points={points} />)}
    </svg>
  </div>;
}

export function projectTriangles(triangles: number[][][], rotationDegrees: number, sectionPercent = 100): string[] {
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
