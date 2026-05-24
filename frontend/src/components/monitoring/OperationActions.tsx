import { OperationActionParameterFields } from "../common/OperationActionParameterFields";
import { formatCapabilityStatus } from "./formatters";
import type {
  OperationAction,
  OperationActionExecutionAttempt,
  OperationActionPreview,
  OperationActionPreviewRecord,
  OperationCapability,
} from "../../types";

export function OperationActions({
  actions,
  capabilities,
  values,
  preview,
  executionAttempt,
  executionHistory,
  actionHistory,
  confirmationPhrase,
  loading,
  canSendCommands,
  onPreview,
  onPreflight,
  onParameterChange,
  onPhraseChange,
  onValidateExecutionGate,
}: {
  actions: OperationAction[];
  capabilities: OperationCapability[];
  values: Record<string, Record<string, string>>;
  preview: OperationActionPreview | null;
  executionAttempt: OperationActionExecutionAttempt | null;
  executionHistory: OperationActionExecutionAttempt[];
  actionHistory: OperationActionPreviewRecord[];
  confirmationPhrase: string;
  loading: boolean;
  canSendCommands: boolean;
  onPreview: (action: OperationAction) => void | Promise<void>;
  onPreflight: (action: OperationAction) => void | Promise<void>;
  onParameterChange: (actionId: string, parameterName: string, value: string) => void;
  onPhraseChange: (value: string) => void;
  onValidateExecutionGate: () => void | Promise<void>;
}) {
  const recentExecutions = executionHistory.slice(0, 3);
  const recentPreviews = actionHistory.slice(0, 3);

  return (
    <div className="operation-actions-layout">
      <div className="operation-capabilities">
        {capabilities.length === 0 ? <p className="muted">Sem capabilities retornadas para esta impressora.</p> : null}
        {capabilities.map((capability) => (
          <div key={capability.action_id} className={`operation-capability ${capability.status}`}>
            <strong>{capability.action_id}</strong>
            <span>{formatCapabilityStatus(capability.status)}</span>
            <small>{capability.reason}</small>
          </div>
        ))}
      </div>

      <div className="operation-actions">
        {actions.length === 0 ? <p className="muted">Nenhuma ação operacional retornada pelo backend.</p> : null}
        {actions.map((action) => (
          <div key={action.id} className="operation-action-card">
            <span>
              <strong>{action.label}</strong>
              <code>{action.id}</code>
            </span>
            <small>
              {action.group} · risco {action.risk}
              {action.block_reason ? ` · ${action.block_reason}` : ""}
            </small>
            <OperationActionParameterFields action={action} values={values[action.id] ?? {}} onChange={onParameterChange} />
            <div className="operation-action-buttons">
              <button type="button" className="secondary-button compact" onClick={() => void onPreflight(action)} disabled={loading}>
                Validar
              </button>
              <button type="button" className="secondary-button compact" onClick={() => void onPreview(action)} disabled={loading}>
                Prévia
              </button>
            </div>
          </div>
        ))}
      </div>

      {preview ? (
        <div className="operation-preview">
          <div>
            <strong>{preview.action.label}</strong>
            <span>{preview.executable ? "Executável após confirmação" : "Bloqueada"}</span>
          </div>
          {preview.blockers.length > 0 ? (
            <ul>
              {preview.blockers.map((blocker) => (
                <li key={blocker}>{blocker}</li>
              ))}
            </ul>
          ) : null}
          <pre>{preview.command_preview.length ? preview.command_preview.join("\n") : "Sem comandos planejados."}</pre>
          <div className="operation-execution-gate">
            <label>
              <span>Confirmação</span>
              <input
                value={confirmationPhrase}
                onChange={(event) => onPhraseChange(event.target.value)}
                placeholder={preview.confirmation_phrase}
                disabled={!preview.executable || !canSendCommands}
              />
            </label>
            <button type="button" className="primary-button" onClick={() => void onValidateExecutionGate()} disabled={loading || !preview.executable || !canSendCommands}>
              Executar
            </button>
          </div>
        </div>
      ) : null}

      {executionAttempt ? (
        <div className="operation-execution-result">
          <strong>Última tentativa: {executionAttempt.status}</strong>
          <span>{executionAttempt.block_reason || (executionAttempt.confirmation_matched ? "Confirmação validada." : "Confirmação não validada.")}</span>
          <small>{executionAttempt.created_at}</small>
        </div>
      ) : null}

      <div className="operation-history">
        <div className="operation-history-heading">
          <strong>Histórico recente</strong>
          <span>Prévia</span>
          <span>Execução</span>
        </div>
        {(recentPreviews.length || recentExecutions.length) ? (
          Array.from({ length: Math.max(recentPreviews.length, recentExecutions.length) }).map((_, index) => {
            const previewRow = recentPreviews[index];
            const executionRow = recentExecutions[index];
            return (
              <div key={`${previewRow?.id ?? "p"}-${executionRow?.id ?? "e"}-${index}`} className="operation-history-row">
                <div>
                  <strong>{previewRow?.action_label ?? executionRow?.action_id ?? "-"}</strong>
                  <small>{previewRow?.created_at ?? executionRow?.created_at ?? "-"}</small>
                </div>
                <span>{previewRow ? (previewRow.executable ? "executável" : "bloqueada") : "-"}</span>
                <span>{executionRow?.status ?? "-"}</span>
              </div>
            );
          })
        ) : (
          <p className="muted">Sem histórico operacional recente.</p>
        )}
      </div>
    </div>
  );
}
