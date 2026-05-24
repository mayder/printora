import React from "react";
import { Activity, AlertTriangle, Crosshair, Database, Gauge, Radio, RefreshCw, ShieldCheck, SlidersHorizontal, Thermometer, Wind, Zap } from "lucide-react";
import { FactGrid, LoadMeter, MonitorBadge, RadialProgress } from "./common";
import { OperationActions } from "./OperationActions";
import { TemperatureMonitor, buildTemperatureSeries } from "./temperature";
import { buildExtruderFacts, buildToolheadFacts, canTone, formatCanAlert, formatDataState, formatDecision, formatOptional, formatTemperature, healthTone } from "./formatters";
import type { CanBusRecord, CanBusRecordComparison, CanBusSummary, HealthResponse } from "./types";
import type {
  OperationAction,
  OperationActionExecutionAttempt,
  OperationActionPreview,
  OperationActionPreviewRecord,
  OperationStatusResponse,
} from "../../types";

export function MonitoringDashboard({
  selectedPrinterName,
  operationStatus,
  operationActionHistory,
  operationActionParameters,
  operationActionPreview,
  operationExecutionAttempt,
  operationExecutionHistory,
  operationExecutionPhrase,
  health,
  canSummary,
  canRecords,
  canComparison,
  loading,
  onRefresh,
  onLoadOfflineFixture,
  onCompareCan,
  onPreviewAction,
  onPreflightAction,
  onActionParameterChange,
  onExecutionPhraseChange,
  onValidateExecutionGate,
}: {
  selectedPrinterName: string;
  operationStatus: OperationStatusResponse | null;
  operationActionHistory: OperationActionPreviewRecord[];
  operationActionParameters: Record<string, Record<string, string>>;
  operationActionPreview: OperationActionPreview | null;
  operationExecutionAttempt: OperationActionExecutionAttempt | null;
  operationExecutionHistory: OperationActionExecutionAttempt[];
  operationExecutionPhrase: string;
  health: HealthResponse | null;
  canSummary: CanBusSummary | null;
  canRecords: CanBusRecord[];
  canComparison: CanBusRecordComparison | null;
  loading: boolean;
  onRefresh: () => void;
  onLoadOfflineFixture: () => void | Promise<void>;
  onCompareCan: () => void;
  onPreviewAction: (action: OperationAction) => void | Promise<void>;
  onPreflightAction: (action: OperationAction) => void | Promise<void>;
  onActionParameterChange: (actionId: string, parameterName: string, value: string) => void;
  onExecutionPhraseChange: (value: string) => void;
  onValidateExecutionGate: () => void | Promise<void>;
}) {
  const temperatureSeries = buildTemperatureSeries(operationStatus?.temperature_history ?? [], operationStatus?.temperatures ?? []);
  const fans = operationStatus?.miscellaneous.fans ?? [];
  const latestCanRecords = canRecords.slice(0, 4);
  const hotend = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("extruder"));
  const bed = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("bed"));
  const actions = operationStatus?.actions ?? [];
  const capabilities = operationStatus?.capabilities ?? [];
  const toolheadFacts = buildToolheadFacts(operationStatus);
  const extruderFacts = buildExtruderFacts(operationStatus);

  return (
    <article className="panel wide panel-section panel-monitoring monitoring-dashboard">
      <div className="panel-heading monitoring-heading">
        <div>
          <h2>Operação em tempo real</h2>
          <p className="muted">{operationStatus?.summary ?? "Aguardando leitura da impressora selecionada."}</p>
        </div>
        <div className="panel-actions">
          <span className="live-pill">Atualiza sozinho</span>
          <button type="button" className="secondary-button" onClick={onRefresh} disabled={loading}>
            <RefreshCw size={15} />
            Atualizar agora
          </button>
          <button type="button" className="secondary-button" onClick={() => void onLoadOfflineFixture()} disabled={loading}>
            <Database size={15} />
            Exemplo offline
          </button>
        </div>
      </div>

      <div className="monitor-status-strip">
        <MonitorBadge icon={Radio} label="Impressora" value={selectedPrinterName} tone={operationStatus?.connected ? "ok" : "danger"} />
        <MonitorBadge icon={Radio} label="Moonraker" value={operationStatus?.connected ? "online" : "offline"} tone={operationStatus?.connected ? "ok" : "danger"} />
        <MonitorBadge icon={Gauge} label="Estado" value={operationStatus?.miscellaneous.print_state ?? "-"} tone={operationStatus?.connected ? "ok" : "warning"} />
        <MonitorBadge icon={AlertTriangle} label="Risco" value={formatDecision(health?.decision)} tone={healthTone(health?.decision)} />
        <MonitorBadge icon={ShieldCheck} label="Modo" value={operationStatus?.safe_mode ?? "read only"} />
        <MonitorBadge icon={Zap} label="Comandos" value={operationStatus?.can_send_commands ? "habilitados" : "bloqueados"} tone={operationStatus?.can_send_commands ? "warning" : "ok"} />
        <MonitorBadge icon={Thermometer} label="Hotend" value={formatTemperature(hotend?.temperature)} />
        <MonitorBadge icon={Thermometer} label="Mesa" value={formatTemperature(bed?.temperature)} />
        <MonitorBadge icon={Database} label="Origem" value={formatDataState(operationStatus?.data_state)} />
      </div>

      {operationStatus?.data_state === "offline" ? (
        <div className="monitor-warning">
          <AlertTriangle size={17} />
          <span>{operationStatus.error ?? "Sem leitura ao vivo. Verifique se a impressora está ligada e na rede."}</span>
        </div>
      ) : null}
      {operationStatus?.data_state === "fixture" ? (
        <div className="monitor-note">
          <Database size={17} />
          <span>Dados simulados para validar layout com a impressora desligada. Nenhum endpoint da impressora foi chamado.</span>
        </div>
      ) : null}
      {operationStatus?.data_state === "last_snapshot" ? (
        <div className="monitor-note">
          <Database size={17} />
          <span>
            Último estado conhecido: snapshot #{operationStatus.last_snapshot?.id ?? "-"} de {operationStatus.last_snapshot?.created_at ?? "-"}.
          </span>
        </div>
      ) : null}

      <div className="monitor-grid">
        <section className="monitor-card monitor-card-wide">
          <div className="monitor-card-title">
            <Thermometer size={18} />
            <h3>Temperaturas</h3>
          </div>
          <TemperatureMonitor temperatures={operationStatus?.temperatures ?? []} series={temperatureSeries} />
        </section>

        <section className="monitor-card">
          <div className="monitor-card-title">
            <Crosshair size={18} />
            <h3>Toolhead</h3>
          </div>
          <FactGrid items={toolheadFacts} />
        </section>

        <section className="monitor-card">
          <div className="monitor-card-title">
            <SlidersHorizontal size={18} />
            <h3>Extrusor</h3>
          </div>
          <FactGrid items={extruderFacts} />
        </section>

        <section className="monitor-card">
          <div className="monitor-card-title">
            <Gauge size={18} />
            <h3>Impressão</h3>
          </div>
          <RadialProgress value={operationStatus?.miscellaneous.progress ?? 0} />
          <div className="monitor-facts">
            <span>Arquivo</span>
            <strong>{operationStatus?.miscellaneous.filename || "-"}</strong>
            <span>Mensagem</span>
            <strong>{operationStatus?.miscellaneous.message || "-"}</strong>
          </div>
        </section>

        <section className="monitor-card">
          <div className="monitor-card-title">
            <Activity size={18} />
            <h3>Sistema</h3>
          </div>
          <div className="load-list">
            {operationStatus?.system_loads.length ? null : <p className="muted">Sem métricas do host nesta leitura.</p>}
            {operationStatus?.system_loads.map((metric) => (
              <LoadMeter key={metric.label} metric={metric} />
            ))}
          </div>
        </section>

        <section className="monitor-card">
          <div className="monitor-card-title">
            <Wind size={18} />
            <h3>Fans</h3>
          </div>
          <div className="fan-monitor-list">
            {fans.length === 0 ? <p className="muted">Nenhum fan retornado pelo Moonraker.</p> : null}
            {fans.map((fan) => (
              <LoadMeter
                key={fan.name}
                metric={{
                  label: fan.name,
                  value: typeof fan.speed === "number" ? fan.speed * 100 : null,
                  unit: "%",
                }}
                detail={`RPM ${fan.rpm ?? "-"}`}
              />
            ))}
          </div>
        </section>

        <section className="monitor-card monitor-card-wide">
          <div className="monitor-card-title">
            <Radio size={18} />
            <h3>CAN</h3>
          </div>
          <div className="can-monitor-header">
            <MonitorBadge label="Estado" value={formatCanAlert(canSummary?.overall_alert ?? latestCanRecords[0]?.alert_level ?? "ok")} tone={canTone(canSummary?.overall_alert ?? latestCanRecords[0]?.alert_level)} />
            <MonitorBadge label="OK" value={String(canSummary?.counts.ok ?? 0)} />
            <MonitorBadge label="Atenção" value={String(canSummary?.counts.monitorar ?? 0)} tone="warning" />
            <MonitorBadge label="Problemas" value={String(canSummary?.counts.problema ?? 0)} tone="danger" />
            <button type="button" className="secondary-button compact" onClick={onCompareCan} disabled={loading || canRecords.length < 2}>
              Comparar leituras
            </button>
          </div>
          {canSummary?.data_state === "no_data" || latestCanRecords.length === 0 ? (
            <p className="muted">Sem leituras CAN registradas para exibir evolução.</p>
          ) : null}
          {canComparison ? (
            <div className={`monitor-can-comparison ${canComparison.alert_level}`}>
              <strong>Última comparação</strong>
              <span>
                {canComparison.interface_name}: rx {formatOptional(canComparison.delta_rx_error)} · tx {formatOptional(canComparison.delta_tx_error)} · retries {formatOptional(canComparison.delta_tx_retries)}
              </span>
              <small>{canComparison.diagnosis}</small>
            </div>
          ) : null}
          <div className="can-monitor-list">
            {latestCanRecords.map((record) => (
              <div key={record.id} className={`can-monitor-row ${record.alert_level}`}>
                <strong>{record.interface_name}</strong>
                <span>rx {record.rx_error} · tx {record.tx_error} · retries {record.tx_retries}</span>
                <small>{record.recorded_at}</small>
                <small>{record.diagnosis}</small>
              </div>
            ))}
          </div>
        </section>

        <section className="monitor-card monitor-card-wide operation-command-center">
          <div className="monitor-card-title">
            <ShieldCheck size={18} />
            <h3>Ações protegidas</h3>
          </div>
          <OperationActions
            actions={actions}
            capabilities={capabilities}
            values={operationActionParameters}
            preview={operationActionPreview}
            executionAttempt={operationExecutionAttempt}
            executionHistory={operationExecutionHistory}
            actionHistory={operationActionHistory}
            confirmationPhrase={operationExecutionPhrase}
            loading={loading}
            canSendCommands={Boolean(operationStatus?.can_send_commands)}
            onPreview={onPreviewAction}
            onPreflight={onPreflightAction}
            onParameterChange={onActionParameterChange}
            onPhraseChange={onExecutionPhraseChange}
            onValidateExecutionGate={onValidateExecutionGate}
          />
        </section>
      </div>
    </article>
  );
}
