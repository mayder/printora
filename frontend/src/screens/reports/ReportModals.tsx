import { CheckCircle2, X } from "lucide-react";
import type React from "react";

export type ReportModalKind = "backup-policy" | "backup-compare" | "restore-plan" | "sanitized-report" | null;

type ReportModalsProps = {
  activeModal: ReportModalKind;
  backupCompareBasePath: string;
  backupCompareTargetPath: string;
  backupDestinationPath: string;
  backupDryRunOnly: boolean;
  backupName: string;
  backupRestoreArchivePath: string;
  backupRestoreConfirmation: string;
  backupRestoreFiles: string;
  backupRestoreRoot: string;
  backupSourcePath: string;
  compareBackupArchives: () => Promise<void>;
  createBackupPolicy: (event: React.FormEvent<HTMLFormElement>) => Promise<void>;
  createBackupRestorePlan: () => Promise<void>;
  loadSanitizedReport: () => Promise<void>;
  loading: boolean;
  onClose: () => void;
  sanitizedMarkdown: string | null;
  selectedPrinterId: number | null;
  setBackupCompareBasePath: (value: string) => void;
  setBackupCompareTargetPath: (value: string) => void;
  setBackupDestinationPath: (value: string) => void;
  setBackupDryRunOnly: (value: boolean) => void;
  setBackupName: (value: string) => void;
  setBackupRestoreArchivePath: (value: string) => void;
  setBackupRestoreConfirmation: (value: string) => void;
  setBackupRestoreFiles: (value: string) => void;
  setBackupRestoreRoot: (value: string) => void;
  setBackupSourcePath: (value: string) => void;
  validateBackupRestoreGate: () => Promise<void>;
};

export function ReportModals(props: ReportModalsProps) {
  const { activeModal, onClose } = props;
  if (!activeModal) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={modalTitle(activeModal)}>
      <div className="modal-card report-modal-card">
        <div className="modal-header">
          <div>
            <h2>{modalTitle(activeModal)}</h2>
            <p>{modalDescription(activeModal)}</p>
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            <X size={16} />
            Fechar
          </button>
        </div>
        {activeModal === "backup-policy" ? <BackupPolicyForm {...props} /> : null}
        {activeModal === "backup-compare" ? <BackupCompareForm {...props} /> : null}
        {activeModal === "restore-plan" ? <RestorePlanForm {...props} /> : null}
        {activeModal === "sanitized-report" ? <SanitizedReportPreview {...props} /> : null}
      </div>
    </div>
  );
}

function BackupPolicyForm({
  backupDestinationPath,
  backupDryRunOnly,
  backupName,
  backupSourcePath,
  createBackupPolicy,
  loading,
  onClose,
  selectedPrinterId,
  setBackupDestinationPath,
  setBackupDryRunOnly,
  setBackupName,
  setBackupSourcePath,
}: ReportModalsProps) {
  return (
    <form className="report-modal-form" onSubmit={(event) => void createBackupPolicy(event).then(onClose)}>
      <label className="form-field">
        <span>Nome da política</span>
        <input value={backupName} onChange={(event) => setBackupName(event.target.value)} required />
      </label>
      <label className="form-field">
        <span>Pasta de origem</span>
        <input value={backupSourcePath} onChange={(event) => setBackupSourcePath(event.target.value)} required />
      </label>
      <label className="form-field">
        <span>Pasta de destino</span>
        <input value={backupDestinationPath} onChange={(event) => setBackupDestinationPath(event.target.value)} required />
      </label>
      <label className="inline-check">
        <input
          type="checkbox"
          checked={backupDryRunOnly}
          onChange={(event) => setBackupDryRunOnly(event.target.checked)}
        />
        Somente simular. Não copiar arquivos.
      </label>
      <div className="modal-footer">
        <button type="button" className="ghost-button" onClick={onClose}>
          <X size={16} />
          Cancelar
        </button>
        <button type="submit" className="primary-button" disabled={!selectedPrinterId || loading}>
          <CheckCircle2 size={16} />
          Criar política
        </button>
      </div>
    </form>
  );
}

function BackupCompareForm({
  backupCompareBasePath,
  backupCompareTargetPath,
  compareBackupArchives,
  loading,
  onClose,
  setBackupCompareBasePath,
  setBackupCompareTargetPath,
}: ReportModalsProps) {
  return (
    <div className="report-modal-form">
      <label className="form-field">
        <span>Backup base</span>
        <input value={backupCompareBasePath} onChange={(event) => setBackupCompareBasePath(event.target.value)} />
      </label>
      <label className="form-field">
        <span>Backup para comparar</span>
        <input value={backupCompareTargetPath} onChange={(event) => setBackupCompareTargetPath(event.target.value)} />
      </label>
      <div className="modal-footer">
        <button type="button" className="ghost-button" onClick={onClose}>
          <X size={16} />
          Fechar
        </button>
        <button
          type="button"
          className="primary-button"
          onClick={() => void compareBackupArchives()}
          disabled={loading || !backupCompareBasePath || !backupCompareTargetPath}
        >
          Comparar
        </button>
      </div>
    </div>
  );
}

function RestorePlanForm({
  backupRestoreArchivePath,
  backupRestoreConfirmation,
  backupRestoreFiles,
  backupRestoreRoot,
  createBackupRestorePlan,
  loading,
  onClose,
  setBackupRestoreArchivePath,
  setBackupRestoreConfirmation,
  setBackupRestoreFiles,
  setBackupRestoreRoot,
  validateBackupRestoreGate,
}: ReportModalsProps) {
  return (
    <div className="report-modal-form">
      <label className="form-field">
        <span>Arquivo .zip</span>
        <input value={backupRestoreArchivePath} onChange={(event) => setBackupRestoreArchivePath(event.target.value)} />
      </label>
      <label className="form-field">
        <span>Raiz onde seria restaurado</span>
        <input value={backupRestoreRoot} onChange={(event) => setBackupRestoreRoot(event.target.value)} />
      </label>
      <label className="form-field">
        <span>Arquivos a avaliar</span>
        <textarea value={backupRestoreFiles} onChange={(event) => setBackupRestoreFiles(event.target.value)} />
      </label>
      <label className="form-field">
        <span>Confirmação técnica</span>
        <input value={backupRestoreConfirmation} onChange={(event) => setBackupRestoreConfirmation(event.target.value)} />
      </label>
      <div className="modal-footer">
        <button type="button" className="ghost-button" onClick={onClose}>
          <X size={16} />
          Fechar
        </button>
        <button
          type="button"
          onClick={() => void validateBackupRestoreGate()}
          disabled={loading || !backupRestoreArchivePath || !backupRestoreRoot}
        >
          Validar gate
        </button>
        <button
          type="button"
          className="primary-button"
          onClick={() => void createBackupRestorePlan()}
          disabled={loading || !backupRestoreArchivePath || !backupRestoreRoot}
        >
          Planejar restore
        </button>
      </div>
    </div>
  );
}

function SanitizedReportPreview({ loadSanitizedReport, loading, onClose, sanitizedMarkdown, selectedPrinterId }: ReportModalsProps) {
  return (
    <div className="report-modal-form">
      <p className="muted">
        O texto abaixo remove URLs, IPs, caminhos locais e valores sensíveis detectáveis antes de compartilhar diagnóstico.
      </p>
      <pre className="report-preview report-modal-preview">{sanitizedMarkdown ?? "Clique em gerar para montar o relatório."}</pre>
      <div className="modal-footer">
        <button type="button" className="ghost-button" onClick={onClose}>
          <X size={16} />
          Fechar
        </button>
        <button
          type="button"
          className="primary-button"
          onClick={() => void loadSanitizedReport()}
          disabled={!selectedPrinterId || loading}
        >
          Gerar relatório
        </button>
      </div>
    </div>
  );
}

function modalTitle(activeModal: Exclude<ReportModalKind, null>): string {
  const titles: Record<Exclude<ReportModalKind, null>, string> = {
    "backup-policy": "Criar política de backup",
    "backup-compare": "Comparar backups",
    "restore-plan": "Planejar restore seguro",
    "sanitized-report": "Relatório para compartilhar",
  };
  return titles[activeModal];
}

function modalDescription(activeModal: Exclude<ReportModalKind, null>): string {
  const descriptions: Record<Exclude<ReportModalKind, null>, string> = {
    "backup-policy": "Configuração técnica opcional. O padrão é simular antes de copiar qualquer arquivo.",
    "backup-compare": "Compara dois arquivos .zip sem alterar a impressora.",
    "restore-plan": "Mostra o que seria feito em uma restauração, mas o Printora mantém a execução real bloqueada.",
    "sanitized-report": "Gera um Markdown de diagnóstico para enviar a outra pessoa sem expor dados sensíveis.",
  };
  return descriptions[activeModal];
}
