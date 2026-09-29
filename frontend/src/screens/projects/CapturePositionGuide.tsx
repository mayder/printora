import * as React from "react";
import type { PhotoHeightBand } from "../../types/photoCapture";

interface Props {
  activeBand: PhotoHeightBand;
  activePosition?: number;
  directionLabels: string[];
}

const bandCopy: Record<PhotoHeightBand, { label: string; cameraY: number; instruction: string }> = {
  high: {
    label: "De cima",
    cameraY: -34,
    instruction: "Segure a câmera acima do objeto e incline para baixo.",
  },
  middle: {
    label: "Na altura do objeto",
    cameraY: 0,
    instruction: "Mantenha a câmera na metade da altura do objeto.",
  },
  low: {
    label: "De baixo",
    cameraY: 34,
    instruction: "Abaixe a câmera e incline para cima. Não vire o objeto.",
  },
};

const markerPositions = [
  { x: 340, y: 282 },
  { x: 476, y: 250 },
  { x: 548, y: 174 },
  { x: 476, y: 98 },
  { x: 340, y: 66 },
  { x: 204, y: 98 },
  { x: 132, y: 174 },
  { x: 204, y: 250 },
];

export function CapturePositionGuide({ activeBand, activePosition, directionLabels }: Props) {
  const selectedBand = bandCopy[activeBand];
  const selectedDirection = activePosition === undefined ? null : directionLabels[activePosition];

  return (
    <section className="capture-position-guide" aria-labelledby="capture-position-guide-title">
      <div className="capture-position-guide-heading">
        <span>Exemplo visual</span>
        <h5 id="capture-position-guide-title">Onde ficar para tirar cada foto</h5>
        <p>O cubo representa o seu objeto. Fique na posição indicada, aponte para o centro e mantenha o objeto inteiro no quadro.</p>
      </div>
      <div className="capture-position-guide-layout">
        <svg className="capture-position-map" viewBox="0 0 680 350" role="img" aria-labelledby="capture-map-title capture-map-description">
          <title id="capture-map-title">Mapa das oito posições ao redor do objeto</title>
          <desc id="capture-map-description">Um cubo no centro e oito posições numeradas ao redor para orientar frente, diagonais, lados e traseira.</desc>
          <ellipse className="capture-map-orbit" cx="340" cy="174" rx="218" ry="116" />
          <g className={`capture-map-cube capture-map-cube-${activeBand}`}>
            <polygon points="340,116 401,146 340,178 279,146" />
            <polygon points="279,146 340,178 340,252 279,217" />
            <polygon points="340,178 401,146 401,217 340,252" />
            <text x="340" y="205" textAnchor="middle">OBJETO</text>
          </g>
          <g className="capture-map-height" aria-hidden="true">
            <line x1="568" y1="84" x2="568" y2="270" />
            {(["high", "middle", "low"] as PhotoHeightBand[]).map((value) => (
              <g key={value} className={value === activeBand ? "active" : ""}>
                <circle cx="568" cy={value === "high" ? 104 : value === "middle" ? 177 : 250} r="8" />
                <text x="587" y={value === "high" ? 109 : value === "middle" ? 182 : 255}>{bandCopy[value].label}</text>
              </g>
            ))}
          </g>
          <g transform={`translate(0 ${selectedBand.cameraY})`}>
            {markerPositions.map((position, index) => (
              <g className={`capture-map-marker ${activePosition === index ? "active" : ""}`} key={directionLabels[index]} transform={`translate(${position.x} ${position.y})`}>
                <circle r="19" />
                <text textAnchor="middle" y="5">{index + 1}</text>
              </g>
            ))}
          </g>
        </svg>
        <div className="capture-position-legend">
          <div className="capture-position-selected">
            <span>Altura selecionada</span>
            <strong>{selectedBand.label}</strong>
            <p>{selectedBand.instruction}</p>
            {selectedDirection ? <p><strong>Foto {activePosition! + 1}:</strong> {selectedDirection}</p> : null}
          </div>
          <ol>
            {directionLabels.map((label, index) => (
              <li className={activePosition === index ? "active" : ""} key={label}>
                <span>{index + 1}</span>{label}
              </li>
            ))}
          </ol>
        </div>
      </div>
      <p className="capture-position-warning"><strong>Importante:</strong> “De baixo” significa câmera baixa apontada para cima. Não coloque a câmera embaixo da mesa e não mova nem vire o objeto durante esta captura.</p>
    </section>
  );
}
