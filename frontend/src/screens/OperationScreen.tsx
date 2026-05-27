import { Badge, Metric } from "../components/common";
import type { ScreenPropsFor } from "./ScreenProps";

type OperationScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "Database"
  | "Gauge"
  | "Printer"
  | "Radio"
  | "RefreshCw"
  | "ShieldCheck"
  | "buildTemperatureSeries"
  | "error"
  | "formatOperationDataState"
  | "formatOperationValue"
  | "formatPercent"
  | "formatPosition"
  | "formatTemperature"
  | "formatUnknown"
  | "loadOfflineOperationFixture"
  | "loadOperationStatus"
  | "loading"
  | "operationStatus"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "temperatureBarHeight"
>;

export function OperationScreen(props: OperationScreenProps) {
  const {
    AlertTriangle,
    Database,
    Gauge,
    Printer,
    Radio,
    RefreshCw,
    ShieldCheck,
    buildTemperatureSeries,
    error,
    formatOperationDataState,
    formatOperationValue,
    formatPercent,
    formatPosition,
    formatTemperature,
    formatUnknown,
    loadOfflineOperationFixture,
    loadOperationStatus,
    loading,
    operationStatus,
    selectedPrinter,
    selectedPrinterId,
    temperatureBarHeight,
  } = props;

  return (
    <>
        <article className="panel wide panel-section panel-operation">
          <div className="panel-heading">
            <div>
              <h2>Operação read-only</h2>
              <p className="muted">{operationStatus?.summary ?? "Aguardando dados da impressora selecionada."}</p>
            </div>
            <button type="button" className="secondary-button" onClick={() => selectedPrinterId && void loadOperationStatus(selectedPrinterId)} disabled={!selectedPrinterId || loading}>
              <RefreshCw className={loading ? "button-busy-icon" : undefined} size={15} />
              Recarregar
            </button>
            <button type="button" className="secondary-button" onClick={() => void loadOfflineOperationFixture()} disabled={loading}>
              <Database size={15} />
              Exemplo offline
            </button>
          </div>
          <div className="overview-strip dense-toolbar">
            <Badge icon={Printer} label="Impressora" value={selectedPrinter?.name ?? "-"} />
            <Badge icon={Radio} label="Moonraker" value={operationStatus?.connected ? "online" : "offline"} />
            <Badge icon={ShieldCheck} label="Modo" value={operationStatus?.safe_mode ?? "read_only"} />
            <Badge icon={Database} label="Dados" value={formatOperationDataState(operationStatus?.data_state)} />
            <Badge icon={Gauge} label="Comandos" value={operationStatus?.can_send_commands ? "habilitados" : "bloqueados"} />
          </div>
          {operationStatus?.data_state === "offline" ? (
            <div className="operation-state offline">
              <AlertTriangle size={17} />
              <div>
                <strong>Sem leitura ao vivo</strong>
                <span>{operationStatus.error ?? "A impressora pode estar desligada ou fora da rede."}</span>
              </div>
            </div>
          ) : null}
          {operationStatus?.data_state === "fixture" ? (
            <div className="operation-state fixture">
              <Database size={17} />
              <div>
                <strong>Fixture local</strong>
                <span>Dados simulados para validar layout com a impressora desligada. Nenhum endpoint da impressora foi chamado.</span>
              </div>
            </div>
          ) : null}
          {operationStatus?.data_state === "last_snapshot" ? (
            <div className="operation-state last-snapshot">
              <Database size={17} />
              <div>
                <strong>Último estado conhecido</strong>
                <span>
                  Snapshot #{operationStatus.last_snapshot?.id ?? "-"} de {operationStatus.last_snapshot?.created_at ?? "-"}.
                  A impressora não foi consultada ao exibir estes dados.
                </span>
              </div>
            </div>
          ) : null}
          <div className="operation-grid">
            <section className="operation-panel">
              <h3>System Loads</h3>
              <div className="section-summary">
                {operationStatus?.system_loads.map((metric: any) => (
                  <Metric key={metric.label} label={metric.label} value={formatOperationValue(metric.value, metric.unit)} />
                ))}
              </div>
            </section>

            <section className="operation-panel">
              <h3>Temperaturas</h3>
              <div className="temperature-list">
                <div className="list-table-header temperature-row">
                  <strong>Sensor</strong>
                  <span>Leitura</span>
                  <small>Potência</small>
                </div>
                {operationStatus?.temperatures.length === 0 ? <p className="muted">Nenhum heater ou sensor retornado pelo Moonraker.</p> : null}
                {operationStatus?.temperatures.map((item: any) => (
                  <div key={item.name} className="temperature-row">
                    <strong>{item.name}</strong>
                    <span>
                      {formatTemperature(item.temperature)} / alvo {formatTemperature(item.target)}
                    </span>
                    <small>Potência: {formatPercent(item.power)}</small>
                  </div>
                ))}
              </div>
            </section>

            <details className="operation-panel wide-operation-panel collapsible-panel">
              <summary>Histórico de temperaturas</summary>
              <div className="temperature-history">
                {buildTemperatureSeries(operationStatus?.temperature_history ?? []).length === 0 ? (
                  <p className="muted">Nenhum snapshot com temperatura disponível para histórico.</p>
                ) : null}
                {buildTemperatureSeries(operationStatus?.temperature_history ?? []).map((series: any) => (
                  <div key={series.name} className="temperature-history-row">
                    <div className="temperature-history-label">
                      <strong>{series.name}</strong>
                      <span>
                        {formatTemperature(series.min)} - {formatTemperature(series.max)}
                      </span>
                    </div>
                    <div className="temperature-sparkline" aria-label={`Histórico ${series.name}`}>
                      {series.points.map((point: any) => (
                        <span
                          key={`${series.name}-${point.snapshotId}-${point.createdAt}`}
                          style={{ height: `${temperatureBarHeight(point.temperature, series.min, series.max)}%` }}
                          title={`${point.createdAt}: ${formatTemperature(point.temperature)}`}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </details>

            <section className="operation-panel">
              <h3>Toolhead</h3>
              <div className="section-summary">
                <Metric label="Posição" value={formatPosition(operationStatus?.toolhead.position)} />
                <Metric label="Home" value={formatUnknown(operationStatus?.toolhead.homed_axes ?? "-")} />
                <Metric label="Velocidade máx." value={formatOperationValue(operationStatus?.toolhead.max_velocity, "mm/s")} />
                <Metric label="Aceleração máx." value={formatOperationValue(operationStatus?.toolhead.max_accel, "mm/s²")} />
                <Metric label="Speed factor" value={formatPercent(operationStatus?.toolhead.speed_factor)} />
              </div>
            </section>

            <section className="operation-panel">
              <h3>Extruder</h3>
              <div className="section-summary">
                <Metric label="Pressure advance" value={formatUnknown(operationStatus?.extruder.pressure_advance ?? "-")} />
                <Metric label="Smooth time" value={formatOperationValue(operationStatus?.extruder.smooth_time, "s")} />
                <Metric label="Extrusion factor" value={formatPercent(operationStatus?.extruder.extrusion_factor)} />
                <Metric label="Filamento usado" value={formatOperationValue(operationStatus?.extruder.filament_used, "mm")} />
              </div>
            </section>

            <section className="operation-panel wide-operation-panel">
              <h3>Miscellaneous</h3>
              <div className="section-summary">
                <Metric label="Print state" value={operationStatus?.miscellaneous.print_state ?? "-"} />
                <Metric label="Arquivo" value={operationStatus?.miscellaneous.filename || "-"} />
                <Metric label="Progresso" value={formatPercent(operationStatus?.miscellaneous.progress)} />
                <Metric label="Mensagem" value={operationStatus?.miscellaneous.message || "-"} />
              </div>
              <div className="fan-list">
                {operationStatus?.miscellaneous.fans?.length === 0 ? <p className="muted">Nenhum fan retornado pelo Moonraker.</p> : null}
                {operationStatus?.miscellaneous.fans?.map((fan: any) => (
                  <div key={fan.name} className="fan-row">
                    <strong>{fan.name}</strong>
                    <span>{formatPercent(fan.speed)}</span>
                    <small>RPM: {formatUnknown(fan.rpm ?? "-")}</small>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </article>


    </>
  );
}
