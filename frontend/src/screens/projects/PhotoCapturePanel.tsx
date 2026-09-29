import * as React from "react";
import { Camera, Check, CheckCircle2, CircleAlert, Ruler, Upload } from "lucide-react";
import { photoCaptureApi } from "../../services/photoCaptureApi";
import type { PhotoCaptureSession, PhotoHeightBand, PhotoScaleMethod } from "../../types/photoCapture";
import { CapturePositionGuide } from "./CapturePositionGuide";
import { ReconstructionPanel } from "./ReconstructionPanel";
import "../../styles/photo-capture.css";

interface Props {
  projectId: number;
  setError: (message: string | null) => void;
  onModelApproved?: () => Promise<void>;
}

const bandLabels: Record<PhotoHeightBand, string> = {
  low: "De baixo",
  middle: "Na altura do objeto",
  high: "De cima",
};

const captureOrder: PhotoHeightBand[] = ["middle", "high", "low"];

const directionLabels = [
  "Frente",
  "Diagonal da frente, lado direito",
  "Lado direito",
  "Diagonal de trás, lado direito",
  "Trás",
  "Diagonal de trás, lado esquerdo",
  "Lado esquerdo",
  "Diagonal da frente, lado esquerdo",
];

const directionInstructions = [
  "à frente do objeto",
  "na diagonal frontal direita",
  "ao lado direito do objeto",
  "na diagonal traseira direita",
  "atrás do objeto",
  "na diagonal traseira esquerda",
  "ao lado esquerdo do objeto",
  "na diagonal frontal esquerda",
];

const bandInstructions: Record<PhotoHeightBand, string> = {
  middle: "Mantenha a câmera na metade da altura do objeto e aponte para o centro.",
  high: "Levante a câmera e incline levemente para baixo, sem esconder as laterais.",
  low: "Abaixe a câmera e incline levemente para cima, mantendo o objeto inteiro na foto.",
};

const bandDescriptions: Record<PhotoHeightBand, string> = {
  middle: "8 fotos com a câmera alinhada à metade da altura do objeto.",
  high: "8 fotos com a câmera acima do objeto e inclinada para baixo.",
  low: "8 fotos com a câmera baixa e inclinada para cima, sem virar o objeto.",
};

function slotInstruction(slot: Pick<CaptureSlot, "band" | "position">): string {
  const angle = slot.band === "middle"
    ? "na metade da altura"
    : slot.band === "high"
      ? "acima e inclinada para baixo"
      : "baixa e inclinada para cima";
  return `Posicione-se ${directionInstructions[slot.position]}, com a câmera ${angle}.`;
}

interface CaptureSlot {
  index: number;
  band: PhotoHeightBand;
  position: number;
  label: string;
  photo: PhotoCaptureSession["photos"][number] | null;
}

function captureSlots(session: PhotoCaptureSession): CaptureSlot[] {
  const photosByBand = Object.fromEntries(captureOrder.map((value) => [
    value,
    session.photos.filter((photo) => photo.height_band === value).sort((a, b) => a.capture_index - b.capture_index),
  ])) as Record<PhotoHeightBand, PhotoCaptureSession["photos"]>;
  let offset = 0;
  return captureOrder.flatMap((value) => {
    const count = session.required_by_height_band[value];
    const slots = Array.from({ length: count }, (_, position) => ({
      index: offset + position + 1,
      band: value,
      position,
      label: directionLabels[position] ?? `Posição ${position + 1}`,
      photo: photosByBand[value][position] ?? null,
    }));
    offset += count;
    return slots;
  });
}

function recommendedBand(session: PhotoCaptureSession): PhotoHeightBand {
  return captureOrder.find((value) => (
    session.accepted_by_height_band[value] < session.required_by_height_band[value]
  )) ?? "middle";
}

export function PhotoCapturePanel({ projectId, setError, onModelApproved }: Props) {
  const [session, setSession] = React.useState<PhotoCaptureSession | null>(null);
  const [consent, setConsent] = React.useState(false);
  const [band, setBand] = React.useState<PhotoHeightBand>("middle");
  const [busy, setBusy] = React.useState(false);
  const [scaleMethod, setScaleMethod] = React.useState<PhotoScaleMethod>("none");
  const [scaleValue, setScaleValue] = React.useState("");
  const [uncertainty, setUncertainty] = React.useState("1");

  React.useEffect(() => {
    void photoCaptureApi.list().then((rows) => {
      const resumed = rows.find((row) => row.project_id === projectId && ["draft", "review", "ready"].includes(row.status)) ?? null;
      setSession(resumed);
      if (resumed) {
        setBand(recommendedBand(resumed));
        setScaleMethod(resumed.scale_method);
        setScaleValue(resumed.scale_value_mm === null ? "" : String(resumed.scale_value_mm));
        setUncertainty(resumed.scale_uncertainty_mm === null ? "1" : String(resumed.scale_uncertainty_mm));
      }
    }).catch(() => undefined);
  }, [projectId]);

  async function start() {
    if (!consent) return;
    setBusy(true);
    setError(null);
    try {
      const created = await photoCaptureApi.create(projectId);
      setSession(created);
      setBand(recommendedBand(created));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível iniciar a captura.");
    } finally {
      setBusy(false);
    }
  }

  async function uploadSlot(file: File | undefined, slot: CaptureSlot) {
    if (!session || !file) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await photoCaptureApi.upload(session.id, file, slot.photo?.capture_index ?? slot.index, slot.band);
      setSession(updated);
      setBand(recommendedBand(updated));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível guardar as fotos.");
    } finally {
      setBusy(false);
    }
  }

  async function saveScale() {
    if (!session) return;
    setBusy(true);
    try {
      const hasScale = scaleMethod !== "none";
      setSession(await photoCaptureApi.updateScale(
        session.id,
        scaleMethod,
        hasScale ? Number(scaleValue) : null,
        hasScale ? Number(uncertainty) : null,
      ));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível guardar a medida.");
    } finally {
      setBusy(false);
    }
  }

  async function complete() {
    if (!session) return;
    setBusy(true);
    try {
      setSession(await photoCaptureApi.complete(session.id));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Revise as fotos antes de concluir.");
    } finally {
      setBusy(false);
    }
  }

  async function exportPhotos() {
    if (!session) return;
    setBusy(true);
    try {
      const blob = await photoCaptureApi.exportBlob(session.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `captura-${session.id}.zip`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível baixar as fotos.");
    } finally {
      setBusy(false);
    }
  }

  if (!session) {
    return (
      <section className="photo-capture-panel" aria-labelledby="photo-capture-title">
        <div className="photo-capture-heading">
          <Camera size={22} aria-hidden="true" />
          <div><h4 id="photo-capture-title">Digitalizar este objeto</h4><p>Vamos orientar cada volta. Você não precisa conhecer modelagem 3D.</p></div>
        </div>
        <ol className="photo-capture-steps" aria-label="Etapas da digitalização"><li className="active">1. Preparar</li><li>2. Tirar 24 fotos</li><li>3. Informar medida</li><li>4. Criar e revisar modelo</li></ol>
        <div className="photo-capture-summary"><strong>Você fará exatamente 24 fotos</strong><span>São três grupos separados. Cada grupo tem oito campos, um para cada lado do objeto.</span></div>
        <CapturePositionGuide activeBand={band} directionLabels={directionLabels} />
        <section className="photo-capture-protocol" aria-labelledby="capture-protocol-title">
          <div><span>O que será solicitado</span><h5 id="capture-protocol-title">Todos os 24 campos da captura</h5><p>Depois de começar, cada posição abaixo terá seu próprio botão para fotografar ou escolher uma imagem.</p></div>
          <div className="photo-capture-protocol-groups">
            {captureOrder.map((value) => (
              <button type="button" className={band === value ? "active" : ""} onClick={() => setBand(value)} key={value}>
                <strong>{bandLabels[value]}</strong><span>{bandDescriptions[value]}</span><small>Campos 1 a 8: frente, quatro diagonais, dois lados e trás.</small>
              </button>
            ))}
          </div>
        </section>
        <section className="photo-capture-preparation-card" aria-labelledby="capture-preparation-title"><div><span>Antes de começar</span><h5 id="capture-preparation-title">Prepare o local</h5></div><ol className="photo-capture-preparation"><li>Coloque o objeto parado sobre uma superfície firme e deixe espaço para caminhar ao redor.</li><li>Use fundo simples e luz uniforme, sem sombra forte.</li><li>Não mova nem vire o objeto durante as 24 fotos. Não use zoom.</li><li>Mantenha o objeto inteiro, centralizado e nítido em todas as imagens.</li></ol></section>
        <p className="photo-capture-note"><CircleAlert size={16} /> Objetos transparentes, muito brilhantes ou sem textura podem precisar de preparação especial.</p>
        <label className="photo-capture-consent"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /> Confirmo que posso fotografar este objeto e que não há pessoas nas fotos.</label>
        <button type="button" className="primary-button" disabled={!consent || busy} onClick={() => void start()}>{busy ? "Preparando..." : "Começar pelas fotos"}</button>
      </section>
    );
  }

  const slots = captureSlots(session);
  const nextEmptySlot = slots.find((slot) => !slot.photo || slot.photo.issues.length > 0);

  return (
    <section className="photo-capture-panel" aria-labelledby="photo-capture-progress-title">
      <div className="photo-capture-heading">
        {session.status === "ready" ? <CheckCircle2 size={22} /> : <Camera size={22} />}
        <div><h4 id="photo-capture-progress-title">{session.status === "ready" ? "Fotos prontas para reconstrução" : "Fotografe uma volta por vez"}</h4><p>{session.covered_photo_count} de {session.target_photo_count} posições cobertas. {session.accepted_photo_count} fotos aprovadas.</p></div>
      </div>
      <progress max={session.target_photo_count} value={session.covered_photo_count}>{session.covered_photo_count}</progress>
      {session.status !== "ready" ? <>
        <ol className="photo-capture-steps" aria-label="Etapas da digitalização">
          <li>1. Preparar</li><li className="active">2. Tirar 24 fotos</li><li className={session.covered_photo_count === session.target_photo_count ? "active" : ""}>3. Informar medida</li><li>4. Criar e revisar modelo</li>
        </ol>
        <div className="photo-capture-band" role="group" aria-label="Altura da câmera">
          {captureOrder.map((value) => <button type="button" className={band === value ? "active" : ""} aria-pressed={band === value} key={value} onClick={() => setBand(value)}>{bandLabels[value]} <span>{session.accepted_by_height_band[value]} de {session.required_by_height_band[value]}</span></button>)}
        </div>
        <CapturePositionGuide activeBand={band} activePosition={nextEmptySlot?.band === band ? nextEmptySlot.position : undefined} directionLabels={directionLabels} />
        <div className="photo-capture-all-groups">
          {captureOrder.map((groupBand) => <section className={`photo-capture-photo-group ${nextEmptySlot?.band === groupBand ? "current" : ""}`} key={groupBand} aria-labelledby={`capture-group-${groupBand}`}>
            <header><div><span>Grupo {captureOrder.indexOf(groupBand) + 1} de 3</span><h5 id={`capture-group-${groupBand}`}>{bandLabels[groupBand]} — 8 campos</h5><p>{bandInstructions[groupBand]}</p></div><strong>{session.accepted_by_height_band[groupBand]} de {session.required_by_height_band[groupBand]} prontas</strong></header>
            <div className="photo-capture-slot-grid">
          {slots.filter((slot) => slot.band === groupBand).map((slot) => {
            const accepted = !!slot.photo && slot.photo.issues.length === 0;
            const needsReview = !!slot.photo && slot.photo.issues.length > 0;
            return (
              <article className={`photo-capture-slot ${accepted ? "complete" : ""} ${needsReview ? "review" : ""} ${slot === nextEmptySlot ? "next" : ""}`} key={`${slot.band}-${slot.index}`}>
                <div className="photo-capture-slot-number">{accepted ? <Check size={17} /> : slot.position + 1}</div>
                <div><strong>{slot.position + 1}. {slot.label}</strong><span>{slotInstruction(slot)}</span><small>{accepted ? "Foto aprovada" : needsReview ? `Precisa ser refeita. ${slot.photo?.issues.join(" ")}` : slot === nextEmptySlot ? "Este é o próximo campo." : "Será liberado na ordem."}</small></div>
                <label className={`${slot === nextEmptySlot || needsReview ? "primary-button" : "secondary-button"} ${!slot.photo && slot !== nextEmptySlot ? "locked" : ""}`}><Upload size={16} />{slot.photo ? "Refazer" : "Adicionar"}<input type="file" accept="image/jpeg,image/png" capture="environment" disabled={busy || (!slot.photo && slot !== nextEmptySlot)} onChange={(event) => { void uploadSlot(event.target.files?.[0], slot); event.currentTarget.value = ""; }} /></label>
              </article>
            );
          })}
            </div>
          </section>)}
        </div>
        {session.next_actions.length ? <ul className="photo-capture-actions">{session.next_actions.map((action) => <li key={action}>{action}</li>)}</ul> : <p className="success-text">A cobertura está completa.</p>}
        <div className="photo-capture-scale"><Ruler size={20} /><div className="photo-capture-scale-copy"><strong>Qual é o tamanho real?</strong><span>Esta informação permite gerar o modelo no tamanho correto.</span></div><label>Método<select value={scaleMethod} onChange={(event) => setScaleMethod(event.target.value as PhotoScaleMethod)}><option value="none">Vou ajustar o tamanho depois</option><option value="known_measurement">Sei uma medida do objeto</option><option value="marker">Coloquei um marcador de escala</option></select></label>{scaleMethod !== "none" ? <><label>Medida conhecida (mm)<input type="number" min="0.1" value={scaleValue} onChange={(event) => setScaleValue(event.target.value)} /></label><label>Margem de erro (mm)<input type="number" min="0" value={uncertainty} onChange={(event) => setUncertainty(event.target.value)} /></label></> : null}<button type="button" className="secondary-button" disabled={busy || (scaleMethod !== "none" && !scaleValue)} onClick={() => void saveScale()}>{session.scale_confirmed ? "Atualizar medida" : "Confirmar medida"}</button></div>
        <button type="button" className="primary-button" disabled={!session.can_complete || busy} onClick={() => void complete()}>Concluir fotos</button>
        {session.photos.length ? <button type="button" className="secondary-button" disabled={busy} onClick={() => void exportPhotos()}>Baixar minhas fotos</button> : null}
      </> : <><p>As fotos continuam privadas e vinculadas a este projeto.</p><button type="button" className="secondary-button" disabled={busy} onClick={() => void exportPhotos()}>Baixar minhas fotos</button><ReconstructionPanel captureSessionId={session.id} setError={setError} onModelApproved={onModelApproved} /></>}
    </section>
  );
}
