import * as React from "react";
import { Camera, CheckCircle2, CircleAlert, Ruler, Upload } from "lucide-react";
import { photoCaptureApi } from "../../services/photoCaptureApi";
import type { PhotoCaptureSession, PhotoHeightBand, PhotoScaleMethod } from "../../types/photoCapture";
import { ReconstructionPanel } from "./ReconstructionPanel";

interface Props {
  projectId: number;
  setError: (message: string | null) => void;
}

const bandLabels: Record<PhotoHeightBand, string> = {
  low: "De baixo",
  middle: "Na altura do objeto",
  high: "De cima",
};

const captureOrder: PhotoHeightBand[] = ["middle", "high", "low"];

function recommendedBand(session: PhotoCaptureSession): PhotoHeightBand {
  return captureOrder.find((value) => (
    session.accepted_by_height_band[value] < session.required_by_height_band[value]
  )) ?? "middle";
}

export function PhotoCapturePanel({ projectId, setError }: Props) {
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

  async function upload(files: FileList | null) {
    if (!session || !files?.length) return;
    setBusy(true);
    setError(null);
    try {
      let current = session;
      for (const file of Array.from(files)) {
        current = await photoCaptureApi.upload(current.id, file, current.photos.length + 1, band);
      }
      setSession(current);
      setBand(recommendedBand(current));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível guardar as fotos.");
    } finally {
      setBusy(false);
    }
  }

  async function replacePhoto(file: File | undefined, captureIndex: number, photoBand: PhotoHeightBand) {
    if (!session || !file) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await photoCaptureApi.upload(session.id, file, captureIndex, photoBand);
      setSession(updated);
      setBand(recommendedBand(updated));
    } catch (error) {
      setError(error instanceof Error ? error.message : "Não foi possível substituir a foto.");
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
        <ol className="photo-capture-preparation">
          <li>Coloque o objeto parado, com fundo simples e luz uniforme.</li>
          <li>Dê uma volta completa fotografando de perto, sem usar zoom.</li>
          <li>Repita na altura do objeto, de cima e de baixo.</li>
        </ol>
        <p className="photo-capture-note"><CircleAlert size={16} /> Objetos transparentes, muito brilhantes ou sem textura podem precisar de preparação especial.</p>
        <label className="photo-capture-consent"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /> Confirmo que posso fotografar este objeto e que não há pessoas nas fotos.</label>
        <button type="button" className="primary-button" disabled={!consent || busy} onClick={() => void start()}>{busy ? "Preparando..." : "Começar pelas fotos"}</button>
      </section>
    );
  }

  return (
    <section className="photo-capture-panel" aria-labelledby="photo-capture-progress-title">
      <div className="photo-capture-heading">
        {session.status === "ready" ? <CheckCircle2 size={22} /> : <Camera size={22} />}
        <div><h4 id="photo-capture-progress-title">{session.status === "ready" ? "Fotos prontas para reconstrução" : "Fotografe uma volta por vez"}</h4><p>{session.covered_photo_count} de {session.target_photo_count} posições cobertas. {session.accepted_photo_count} fotos aprovadas.</p></div>
      </div>
      <progress max={session.target_photo_count} value={session.covered_photo_count}>{session.covered_photo_count}</progress>
      {session.status !== "ready" ? <>
        <div className="photo-capture-band" role="group" aria-label="Altura da câmera">
          {captureOrder.map((value) => <button type="button" className={band === value ? "active" : ""} aria-pressed={band === value} key={value} onClick={() => setBand(value)}>{bandLabels[value]} <span>{session.accepted_by_height_band[value]} de {session.required_by_height_band[value]}</span></button>)}
        </div>
        <label className="photo-capture-upload"><Upload size={18} /><span>{busy ? "Verificando fotos..." : "Tirar ou escolher fotos"}</span><input type="file" accept="image/jpeg,image/png" capture="environment" multiple disabled={busy} onChange={(event) => void upload(event.target.files)} /></label>
        {session.next_actions.length ? <ul className="photo-capture-actions">{session.next_actions.map((action) => <li key={action}>{action}</li>)}</ul> : <p className="success-text">A cobertura está completa.</p>}
        {session.photos.some((photo) => photo.issues.length) ? <div className="photo-capture-review"><strong>Fotos para refazer</strong>{session.photos.filter((photo) => photo.issues.length).map((photo) => <div className="photo-capture-review-row" key={photo.id}><p>Foto {photo.capture_index}: {photo.issues.join(" ")}</p><label className="secondary-button">Refazer esta foto<input type="file" accept="image/jpeg,image/png" capture="environment" disabled={busy} onChange={(event) => void replacePhoto(event.target.files?.[0], photo.capture_index, photo.height_band)} /></label></div>)}</div> : null}
        <div className="photo-capture-scale"><Ruler size={18} /><label>Escala<select value={scaleMethod} onChange={(event) => setScaleMethod(event.target.value as PhotoScaleMethod)}><option value="none">Continuar sem tamanho real</option><option value="known_measurement">Sei uma medida do objeto</option><option value="marker">Usei um marcador de escala</option></select></label>{scaleMethod !== "none" ? <><label>Medida em mm<input type="number" min="0.1" value={scaleValue} onChange={(event) => setScaleValue(event.target.value)} /></label><label>Margem em mm<input type="number" min="0" value={uncertainty} onChange={(event) => setUncertainty(event.target.value)} /></label></> : null}<button type="button" className="secondary-button" disabled={busy || (scaleMethod !== "none" && !scaleValue)} onClick={() => void saveScale()}>{session.scale_confirmed ? "Atualizar escala" : "Confirmar escala"}</button></div>
        <button type="button" className="primary-button" disabled={!session.can_complete || busy} onClick={() => void complete()}>Concluir fotos</button>
        {session.photos.length ? <button type="button" className="secondary-button" disabled={busy} onClick={() => void exportPhotos()}>Baixar minhas fotos</button> : null}
      </> : <><p>As fotos continuam privadas e vinculadas a este projeto.</p><button type="button" className="secondary-button" disabled={busy} onClick={() => void exportPhotos()}>Baixar minhas fotos</button><ReconstructionPanel captureSessionId={session.id} setError={setError} /></>}
    </section>
  );
}
