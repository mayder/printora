import React from "react";
import { Download, Upload } from "lucide-react";
import {
  slicingApi,
  type NativeSlicingProfileBundle,
  type SlicingProfileBundle,
  type SlicingProfileDiff,
} from "../../services/slicingApi";

type Props = { setError: (message: string | null) => void };

export function SlicingProfilesPanel({ setError }: Props) {
  const [bundles, setBundles] = React.useState<SlicingProfileBundle[]>([]);
  const [targetBundleId, setTargetBundleId] = React.useState("");
  const [title, setTitle] = React.useState("");
  const [engineVersion, setEngineVersion] = React.useState("");
  const [nativeBundle, setNativeBundle] = React.useState<NativeSlicingProfileBundle | null>(null);
  const [fileName, setFileName] = React.useState("");
  const [difference, setDifference] = React.useState<SlicingProfileDiff | null>(null);
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(async () => {
    try {
      setBundles(await slicingApi.profileBundles());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar perfis de fatiamento");
    }
  }, [setError]);

  React.useEffect(() => {
    void load();
  }, [load]);

  async function readFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text()) as Record<string, unknown>;
      const candidate = (parsed.native_bundle ?? parsed) as Partial<NativeSlicingProfileBundle>;
      if (!isRecord(candidate.machine) || !isRecord(candidate.process) || !isRecord(candidate.filament)) {
        throw new Error("O arquivo precisa reunir os perfis de impressora, qualidade e material.");
      }
      setNativeBundle(candidate as NativeSlicingProfileBundle);
      setFileName(file.name);
      setTitle((current) => current || cleanFileName(file.name));
      if (typeof parsed.engine_version === "string") setEngineVersion(parsed.engine_version);
      setError(null);
    } catch (err) {
      setNativeBundle(null);
      setFileName("");
      setError(err instanceof Error ? err.message : "Arquivo de perfil inválido");
    } finally {
      event.target.value = "";
    }
  }

  async function importBundle(event: React.FormEvent) {
    event.preventDefault();
    if (!nativeBundle) return;
    const target = bundles.find((bundle) => bundle.id === Number(targetBundleId));
    setBusy(true);
    try {
      await slicingApi.importProfileBundle({
        title: title.trim(),
        engine_version: engineVersion.trim(),
        native_bundle: nativeBundle,
        bundle_id: target?.id ?? null,
        parent_revision_id: target?.current_revision_id ?? null,
      });
      setNativeBundle(null);
      setFileName("");
      setDifference(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao importar o perfil");
    } finally {
      setBusy(false);
    }
  }

  async function compare(bundle: SlicingProfileBundle) {
    if (bundle.revisions.length < 2) return;
    setBusy(true);
    try {
      setDifference(await slicingApi.compareProfileRevisions(bundle.revisions[1].id, bundle.revisions[0].id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao comparar versões");
    } finally {
      setBusy(false);
    }
  }

  async function download(bundle: SlicingProfileBundle) {
    if (!bundle.current_revision_id) return;
    setBusy(true);
    try {
      const exported = await slicingApi.exportProfileRevision(bundle.current_revision_id);
      const url = URL.createObjectURL(new Blob([JSON.stringify(exported, null, 2)], { type: "application/json" }));
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${slug(bundle.title)}-v${bundle.revisions[0]?.revision_number ?? 1}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao baixar o perfil");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="print-project-detail-section" aria-labelledby="slicing-profiles-title">
      <h4 id="slicing-profiles-title">Perfis de fatiamento</h4>
      <p className="muted">Guarde juntos a impressora, a qualidade e o material. Cada alteração vira uma versão e os trabalhos antigos continuam reproduzíveis.</p>
      <form className="print-project-form" onSubmit={(event) => void importBundle(event)}>
        <label>
          O que deseja fazer?
          <select value={targetBundleId} onChange={(event) => {
            const next = event.target.value;
            const selected = bundles.find((bundle) => bundle.id === Number(next));
            setTargetBundleId(next);
            if (selected) {
              setTitle(selected.title);
              setEngineVersion(selected.engine_version);
            }
          }} disabled={busy}>
            <option value="">Criar um novo perfil</option>
            {bundles.map((bundle) => <option key={bundle.id} value={bundle.id}>Atualizar {bundle.title}</option>)}
          </select>
        </label>
        <label>
          Nome fácil de reconhecer
          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Ex.: Voron com PLA — qualidade" disabled={busy} required />
        </label>
        <label>
          Versão do OrcaSlicer
          <input value={engineVersion} onChange={(event) => setEngineVersion(event.target.value)} placeholder="Ex.: 2.3.1" disabled={busy} required />
        </label>
        <label className="secondary-button file-button">
          <Upload size={16} />
          {fileName || "Escolher arquivo JSON"}
          <input type="file" accept="application/json,.json" onChange={(event) => void readFile(event)} disabled={busy} />
        </label>
        <button type="submit" className="primary-button" disabled={busy || !nativeBundle || !title.trim() || !engineVersion.trim()}>
          Guardar perfil
        </button>
      </form>
      {bundles.length === 0 ? <p className="muted">Nenhum perfil executável importado.</p> : (
        <div className="print-project-job-list">
          {bundles.map((bundle) => (
            <div className="print-project-job-row" key={bundle.id}>
              <div>
                <strong>{bundle.title}</strong>
                <span>OrcaSlicer {bundle.engine_version} · versão {bundle.revisions[0]?.revision_number ?? 1}</span>
                <small>Identificação {bundle.current_sha256?.slice(0, 12) ?? "indisponível"}</small>
              </div>
              <div className="print-project-job-actions">
                {bundle.revisions.length > 1 ? <button type="button" className="secondary-button" onClick={() => void compare(bundle)} disabled={busy}>Comparar versões</button> : null}
                <button type="button" className="secondary-button" onClick={() => void download(bundle)} disabled={busy}><Download size={15} />Baixar cópia</button>
              </div>
            </div>
          ))}
        </div>
      )}
      {difference ? (
        <div className="print-project-slicing-warning" role="status">
          Comparação pronta: {Object.keys(difference.added).length} adicionado(s), {Object.keys(difference.changed).length} alterado(s) e {Object.keys(difference.removed).length} removido(s).
        </div>
      ) : null}
    </section>
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function cleanFileName(name: string): string {
  return name.replace(/\.json$/i, "").replace(/[-_]+/g, " ").trim();
}

function slug(value: string): string {
  return value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "perfil";
}
