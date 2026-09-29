import type { TactileFormat } from "../types/accessibility";


const SAFE_TITLE = "Referência tátil Printora";
const DESCRIPTION = "Forma retangular, orientação horizontal, ação principal no canto inferior direito.";

export function buildTactileArtifact(format: TactileFormat): {
  content: string;
  mimeType: string;
  fileName: string;
} {
  if (format === "brf") {
    return {
      content: `${SAFE_TITLE}\n${DESCRIPTION}\n`,
      mimeType: "text/plain;charset=utf-8",
      fileName: "printora-referencia-tatil.brf",
    };
  }
  return {
    content: [
      '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500" role="img">',
      `<title>${SAFE_TITLE}</title>`,
      `<desc>${DESCRIPTION}</desc>`,
      '<rect x="40" y="40" width="720" height="420" rx="24" fill="none" stroke="black" stroke-width="12"/>',
      '<circle cx="650" cy="370" r="52" fill="none" stroke="black" stroke-width="12"/>',
      '<path d="M120 150H680M120 240H520" fill="none" stroke="black" stroke-width="12"/>',
      "</svg>",
    ].join(""),
    mimeType: "image/svg+xml;charset=utf-8",
    fileName: "printora-referencia-tatil.svg",
  };
}
export function downloadTactileArtifact(format: TactileFormat): void {
  const artifact = buildTactileArtifact(format);
  const url = URL.createObjectURL(new Blob([artifact.content], { type: artifact.mimeType }));
  const link = document.createElement("a");
  link.href = url;
  link.download = artifact.fileName;
  link.click();
  URL.revokeObjectURL(url);
}
