import { Metric } from "../components/common";
import type { ScreenPropsFor } from "./ScreenProps";

type SettingsScreenProps = ScreenPropsFor<
  | "FileText"
  | "History"
  | "RefreshCw"
  | "Settings"
  | "displayedReleaseRows"
  | "formatReleaseSourceStatus"
  | "formatReleaseUpdateStatus"
  | "formatSelfUpdateStatus"
  | "loadSelfUpdateHistory"
  | "loadSystemReleases"
  | "releaseError"
  | "releaseLoading"
  | "releasePanelClass"
  | "releaseStatusPillClass"
  | "selfUpdateHistory"
  | "selfUpdateRunClass"
  | "systemReleases"
>;

export function SettingsScreen(props: SettingsScreenProps) {
  const {
    FileText,
    History,
    RefreshCw,
    Settings,
    displayedReleaseRows,
    formatReleaseSourceStatus,
    formatReleaseUpdateStatus,
    formatSelfUpdateStatus,
    loadSelfUpdateHistory,
    loadSystemReleases,
    releaseError,
    releaseLoading,
    releasePanelClass,
    releaseStatusPillClass,
    selfUpdateHistory,
    selfUpdateRunClass,
    systemReleases,
  } = props;

  return (
    <>
      <article className={`panel wide panel-section panel-settings releases-panel ${releasePanelClass(systemReleases)}`}>
        <div className="panel-header-row">
          <div>
            <h2>Administração do sistema</h2>
            <p>
              Versão publicada, canal, status da plataforma e changelog do Printora. Ações de impressora e agente ficam
              dentro dos respectivos registros.
            </p>
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={() => void loadSystemReleases()}
            disabled={releaseLoading}
          >
            <RefreshCw className={releaseLoading ? "button-busy-icon" : undefined} size={16} />
            {releaseLoading ? "Verificando" : "Verificar releases"}
          </button>
        </div>
        <div className="release-summary-grid">
          <Metric label="Versão publicada" value={systemReleases?.installed_version ?? "-"} />
          <Metric label="Última release" value={systemReleases?.latest_release?.tag ?? "-"} />
          <Metric label="Canal" value={systemReleases?.channel ?? "-"} />
          <Metric label="Status" value={formatReleaseUpdateStatus(systemReleases, releaseLoading, releaseError)} />
        </div>
        {releaseError ? (
          <div className="action-result warning">
            <strong>Erro de rede</strong>
            <span>{releaseError}</span>
          </div>
        ) : null}
        {systemReleases?.error ? (
          <div className="action-result warning">
            <strong>{formatReleaseSourceStatus(systemReleases.status)}</strong>
            <span>{systemReleases.error}</span>
          </div>
        ) : null}
        {systemReleases?.latest_release ? (
          <div className="release-latest-card">
            <div>
              <span className={`status-pill ${releaseStatusPillClass(systemReleases)}`}>
                {formatReleaseUpdateStatus(systemReleases, false, null)}
              </span>
              <strong>{systemReleases.latest_release.name}</strong>
              <small>
                {systemReleases.latest_release.tag} · {systemReleases.latest_release.published_at ?? "sem data"} ·{" "}
                {systemReleases.latest_release.channel}
              </small>
            </div>
            <p>{systemReleases.latest_release.changelog_summary || "Sem changelog informado."}</p>
          </div>
        ) : (
          <div className="release-latest-card">
            <div>
              <span className="status-pill">aguardando</span>
              <strong>Status da plataforma ainda não carregado</strong>
              <small>Use verificar releases para consultar o estado publicado.</small>
            </div>
            <p>Em cloud, esta tela é informativa para operador. Update da plataforma é rotina administrativa.</p>
          </div>
        )}
      </article>

      <article className="panel wide panel-section panel-settings">
        <div className="panel-header-row">
          <div>
            <h2>Escopo global</h2>
            <p>Itens técnicos específicos saíram desta tela para evitar misturar plataforma, impressora e host do agente.</p>
          </div>
          <Settings size={20} />
        </div>
        <div className="release-summary-grid">
          <Metric label="Plataforma" value="Printora Cloud" />
          <Metric label="Operação" value="por impressora" />
          <Metric label="Diagnóstico host" value="por agente" />
          <Metric label="CAN técnico" value="por impressora" />
        </div>
      </article>

      <details className="panel panel-section panel-settings collapsible-panel settings-advanced-panel release-history-panel">
        <summary className="settings-advanced-summary">
          <span>Releases anteriores</span>
        </summary>
        <div className="release-list">
          {releaseLoading ? <p className="muted">Carregando releases de produção...</p> : null}
          {!releaseLoading && displayedReleaseRows.length === 0 ? (
            <p className="muted">Nenhuma release anterior para listar.</p>
          ) : null}
          {displayedReleaseRows.map((release: any) => (
            <div key={release.tag} className={`release-row ${release.installed ? "installed" : ""}`}>
              <div>
                <strong>{release.name}</strong>
                <span>
                  {release.tag} · {release.published_at ?? "sem data"} · {release.installed ? "publicada" : release.channel}
                </span>
              </div>
              <p>{release.changelog_summary || "Sem changelog informado."}</p>
            </div>
          ))}
        </div>
      </details>

      <details className="panel panel-section panel-settings collapsible-panel settings-advanced-panel self-update-history">
        <summary className="settings-advanced-summary">
          <span>Histórico da plataforma</span>
          <button
            type="button"
            className="secondary-button compact-summary-action"
            onClick={(event) => {
              event.preventDefault();
              event.stopPropagation();
              void loadSelfUpdateHistory();
            }}
          >
            <History size={15} />
            Recarregar
          </button>
        </summary>
        <p className="muted">Histórico administrativo do Printora. Update e rollback da plataforma não são operação do usuário final.</p>
        {selfUpdateHistory.length === 0 ? <p className="muted">Nenhum update do Printora registrado.</p> : null}
        {selfUpdateHistory.slice(0, 5).map((run: any) => (
          <div key={run.id} className={`update-row ${selfUpdateRunClass(run.status)}`}>
            <div className="update-main">
              <div>
                <strong>#{run.id} · {run.target_tag}</strong>
                <span>
                  {formatSelfUpdateStatus(run.status)} · {run.created_at}
                </span>
              </div>
              <FileText size={16} />
            </div>
          </div>
        ))}
      </details>
    </>
  );
}
