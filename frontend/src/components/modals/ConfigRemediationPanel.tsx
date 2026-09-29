import { FileDiff, RotateCw, ShieldCheck } from "lucide-react";
import type { ConfigRemediationResult } from "../../types";

type ConfigRemediationPanelProps = {
  busy: boolean;
  error: string;
  preview: ConfigRemediationResult | null;
  applyResult: ConfigRemediationResult | null;
  selectedIds: string[];
  onPreview: () => void;
  onApply: () => void;
  onToggle: (targetId: string) => void;
};

export function ConfigRemediationPanel({
  busy,
  error,
  preview,
  applyResult,
  selectedIds,
  onPreview,
  onApply,
  onToggle,
}: ConfigRemediationPanelProps) {
  const candidates = preview?.candidates ?? [];
  const changedCandidates = candidates.filter((candidate) => candidate.changed);
  return (
    <div className="config-remediation-panel">
      <div className="config-remediation-heading">
        <div>
          <strong>Correção segura em arquivo incluído</strong>
          <span>O Printora pode localizar a seção real, mostrar o diff e aplicar com backup.</span>
        </div>
        <button type="button" className="secondary-button" onClick={onPreview} disabled={busy}>
          <FileDiff size={15} />
          {busy && !preview ? "Buscando" : "Ver prévia"}
        </button>
      </div>
      {error ? <small className="calibration-save-config-error">{error}</small> : null}
      {preview ? (
        <>
          <small>
            Seção [{preview.section}] · {changedCandidates.length}/{candidates.length} ocorrência(s) com mudança proposta.
          </small>
          {candidates.map((candidate) => (
            <label key={candidate.id} className={`config-remediation-candidate ${candidate.changed ? "" : "unchanged"}`}>
              <span>
                <input
                  type="checkbox"
                  checked={selectedIds.includes(candidate.id)}
                  onChange={() => onToggle(candidate.id)}
                  disabled={!candidate.changed || busy || applyResult?.status === "applied"}
                />
                <strong>{candidate.path}</strong>
                <small>
                  linhas {candidate.start_line}-{candidate.end_line}
                </small>
              </span>
              <pre>{candidate.diff.length ? candidate.diff.join("\n") : candidate.current}</pre>
            </label>
          ))}
          <div className="config-remediation-actions">
            {applyResult?.status === "applied" ? (
              <small>
                <ShieldCheck size={14} />
                Aplicado com backup em {applyResult.backup_path || "-"}.
              </small>
            ) : (
              <small>
                <RotateCw size={14} />
                Ao aplicar, o Printora cria backup e reinicia o firmware.
              </small>
            )}
            <button
              type="button"
              className="danger-button"
              onClick={onApply}
              disabled={busy || selectedIds.length === 0 || applyResult?.status === "applied"}
            >
              {busy && preview ? "Aplicando" : applyResult?.status === "applied" ? "Aplicado" : "Aplicar e reiniciar"}
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
}
