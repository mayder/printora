import { AlertTriangle, ArrowLeft, CheckCircle2, ClipboardCheck, Pencil, Scale, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";
import type {
  MaterialCompatibilityResult,
  MaterialConsumption,
  MaterialQualitySample,
  MaterialSpool,
  PrinterRecord,
} from "../../types";
import { formatWeight } from "./MaterialSpoolList";

type ConsumptionInput = {
  idempotency_key: string;
  predicted_weight_g?: number | null;
  actual_weight_g?: number | null;
  status: "planned" | "confirmed";
  note?: string;
};

type QualityInput = {
  sample_type: "dimensional" | "calibration";
  metric_name: string;
  nominal_value_mm: number;
  measured_value_mm: number;
  tolerance_mm: number;
  note?: string;
};

type Props = {
  spool: MaterialSpool;
  printers: PrinterRecord[];
  consumptions: MaterialConsumption[];
  qualitySamples: MaterialQualitySample[];
  compatibility: MaterialCompatibilityResult | null;
  busy: boolean;
  onBack: () => void;
  onEdit: () => void;
  onArchive: () => Promise<void>;
  onCheckCompatibility: (input: { printer_id: number; required_weight_g: number | null; ventilation_confirmed: boolean | null }) => Promise<void>;
  onRecordConsumption: (input: ConsumptionInput) => Promise<void>;
  onCreateQuality: (input: QualityInput) => Promise<void>;
};

export function MaterialSpoolDetail(props: Props) {
  const { spool, printers, consumptions, qualitySamples, compatibility, busy, onBack, onEdit, onArchive, onCheckCompatibility, onRecordConsumption, onCreateQuality } = props;
  const [printerId, setPrinterId] = useState("");
  const [requiredWeight, setRequiredWeight] = useState("");
  const [ventilation, setVentilation] = useState<"unknown" | "yes" | "no">("unknown");
  const [consumptionMode, setConsumptionMode] = useState<"planned" | "confirmed">("planned");
  const [consumptionWeight, setConsumptionWeight] = useState("");
  const [consumptionNote, setConsumptionNote] = useState("");
  const [idempotencyKey, setIdempotencyKey] = useState(createIdempotencyKey);
  const [sampleType, setSampleType] = useState<"dimensional" | "calibration">("dimensional");
  const [metricName, setMetricName] = useState("Diâmetro do filamento");
  const [nominalValue, setNominalValue] = useState("1.75");
  const [measuredValue, setMeasuredValue] = useState("");
  const [tolerance, setTolerance] = useState("0.05");
  const compatibilityTone = useMemo(() => compatibility?.status ?? "unknown", [compatibility]);

  async function submitCompatibility(event: React.FormEvent) {
    event.preventDefault();
    if (!printerId) return;
    await onCheckCompatibility({
      printer_id: Number(printerId),
      required_weight_g: parseOptionalNumber(requiredWeight),
      ventilation_confirmed: ventilation === "unknown" ? null : ventilation === "yes",
    });
  }

  async function submitConsumption(event: React.FormEvent) {
    event.preventDefault();
    const weight = Number(consumptionWeight);
    try {
      await onRecordConsumption({
        idempotency_key: idempotencyKey,
        status: consumptionMode,
        predicted_weight_g: consumptionMode === "planned" ? weight : null,
        actual_weight_g: consumptionMode === "confirmed" ? weight : null,
        note: consumptionNote,
      });
    } catch {
      return;
    }
    setConsumptionWeight("");
    setConsumptionNote("");
    setIdempotencyKey(createIdempotencyKey());
  }

  async function submitQuality(event: React.FormEvent) {
    event.preventDefault();
    try {
      await onCreateQuality({
        sample_type: sampleType,
        metric_name: metricName,
        nominal_value_mm: Number(nominalValue),
        measured_value_mm: Number(measuredValue),
        tolerance_mm: Number(tolerance),
      });
    } catch {
      return;
    }
    setMeasuredValue("");
  }

  return (
    <>
      <div className="panel-heading materials-heading">
        <div>
          <button type="button" className="text-button material-back" onClick={onBack}><ArrowLeft size={16} /> Voltar aos spools</button>
          <span className="materials-eyebrow">Material disponível</span>
          <h2>{spool.name}</h2>
          <p className="muted">{[spool.material_type, spool.brand, spool.color_name].filter(Boolean).join(" · ") || "Material sem detalhes adicionais"}</p>
        </div>
        <div className="material-detail-actions">
          {spool.source === "local" ? <button type="button" className="secondary-button" onClick={onEdit}><Pencil size={16} /> Editar</button> : null}
          {spool.source === "local" ? <button type="button" className="danger-button" onClick={() => void onArchive()} disabled={busy}><Trash2 size={16} /> Arquivar</button> : null}
        </div>
      </div>

      <section className="material-summary-grid" aria-label="Resumo do spool">
        <div><span>Disponível</span><strong>{formatWeight(spool.remaining_weight_g)}</strong></div>
        <div><span>Peso inicial</span><strong>{formatWeight(spool.initial_weight_g)}</strong></div>
        <div><span>Guardado em</span><strong>{spool.location || "Não informado"}</strong></div>
        <div><span>Origem</span><strong>{spool.source === "spoolman" ? "Spoolman" : "Printora"}</strong></div>
      </section>

      {spool.source === "spoolman" ? <p className="materials-callout">Este spool é controlado pelo Spoolman. Para alterar peso ou cadastro, faça a mudança nele e sincronize novamente.</p> : null}
      {spool.alerts.length ? <section className="material-alert-list" aria-label="Orientações do material">{spool.alerts.map((alert) => <article key={alert.code}><AlertTriangle size={18} /><div><strong>{alert.title}</strong><p>{alert.detail}</p><span>Próximo passo: {alert.action}</span></div></article>)}</section> : <p className="materials-success"><CheckCircle2 size={17} /> O cadastro não possui alertas conhecidos.</p>}

      <div className="material-work-grid">
        <section className="material-work-card">
          <ClipboardCheck size={22} />
          <h3>Conferir antes de imprimir</h3>
          <p>Escolha a impressora e informe o peso previsto. O Printora só confirma quando os dados necessários estão disponíveis.</p>
          <form onSubmit={(event) => void submitCompatibility(event)}>
            <label><span>Impressora *</span><select required value={printerId} onChange={(event) => setPrinterId(event.target.value)}><option value="">Selecione</option>{printers.map((printer) => <option key={printer.id} value={printer.id}>{printer.name}</option>)}</select></label>
            <label><span>Peso necessário (g)</span><input type="number" min="0" step="0.1" value={requiredWeight} onChange={(event) => setRequiredWeight(event.target.value)} /></label>
            <label><span>O ambiente tem ventilação adequada?</span><select value={ventilation} onChange={(event) => setVentilation(event.target.value as typeof ventilation)}><option value="unknown">Não sei informar</option><option value="yes">Sim</option><option value="no">Não</option></select></label>
            <button type="submit" className="primary-button" disabled={busy || !printerId}>Conferir compatibilidade</button>
          </form>
          {compatibility ? <div className={`material-compatibility ${compatibilityTone}`} aria-live="polite"><strong>{compatibilityLabel(compatibility.status)}</strong>{compatibility.reasons.map((reason) => <p key={reason}>{reason}</p>)}{compatibility.warnings.map((warning) => <p key={warning}>{warning}</p>)}</div> : null}
        </section>

        <section className="material-work-card">
          <Scale size={22} />
          <h3>Registrar uso do material</h3>
          <p>Use “planejado” para uma estimativa. Use “confirmado” apenas depois de conhecer o consumo real.</p>
          <form onSubmit={(event) => void submitConsumption(event)}>
            <label><span>Tipo de registro</span><select value={consumptionMode} onChange={(event) => setConsumptionMode(event.target.value as typeof consumptionMode)}><option value="planned">Uso planejado</option><option value="confirmed">Uso confirmado</option></select></label>
            <label><span>Peso (g) *</span><input required type="number" min="0.1" step="0.1" value={consumptionWeight} onChange={(event) => setConsumptionWeight(event.target.value)} /></label>
            <label><span>Observação</span><input value={consumptionNote} onChange={(event) => setConsumptionNote(event.target.value)} placeholder="Opcional" /></label>
            <button type="submit" className="primary-button" disabled={busy}>Registrar</button>
          </form>
          <div className="material-history"><strong>Últimos registros</strong>{consumptions.length === 0 ? <p>Nenhum uso registrado.</p> : consumptions.slice(0, 5).map((item) => <p key={item.id}><span>{item.status === "confirmed" ? "Confirmado" : item.status === "planned" ? "Planejado" : "Liberado"}</span><b>{formatWeight(item.actual_weight_g ?? item.predicted_weight_g)}</b></p>)}</div>
        </section>

        <section className="material-work-card material-quality-card">
          <ClipboardCheck size={22} />
          <h3>Conferir uma medida</h3>
          <p>Registre uma medição simples. O resultado é calculado pela medida esperada e sua tolerância.</p>
          <form onSubmit={(event) => void submitQuality(event)}>
            <label><span>Tipo</span><select value={sampleType} onChange={(event) => setSampleType(event.target.value as typeof sampleType)}><option value="dimensional">Medida do material</option><option value="calibration">Peça de calibração</option></select></label>
            <label><span>O que foi medido *</span><input required minLength={2} value={metricName} onChange={(event) => setMetricName(event.target.value)} /></label>
            <label><span>Medida esperada (mm) *</span><input required type="number" min="0" step="0.001" value={nominalValue} onChange={(event) => setNominalValue(event.target.value)} /></label>
            <label><span>Medida encontrada (mm) *</span><input required type="number" min="0" step="0.001" value={measuredValue} onChange={(event) => setMeasuredValue(event.target.value)} /></label>
            <label><span>Tolerância (mm) *</span><input required type="number" min="0" step="0.001" value={tolerance} onChange={(event) => setTolerance(event.target.value)} /></label>
            <button type="submit" className="primary-button" disabled={busy}>Salvar medição</button>
          </form>
          <div className="material-history"><strong>Medições recentes</strong>{qualitySamples.length === 0 ? <p>Nenhuma medição registrada.</p> : qualitySamples.slice(0, 5).map((sample) => <p key={sample.id}><span>{sample.metric_name}</span><b className={sample.result === "passed" ? "passed" : "failed"}>{sample.result === "passed" ? "Dentro da tolerância" : "Fora da tolerância"}</b></p>)}</div>
        </section>
      </div>
    </>
  );
}

function compatibilityLabel(status: MaterialCompatibilityResult["status"]) {
  if (status === "compatible") return "Compatível com os dados informados";
  if (status === "incompatible") return "Não use ainda";
  return "Ainda não foi possível confirmar";
}

function parseOptionalNumber(value: string) {
  return value.trim() ? Number(value) : null;
}

function createIdempotencyKey() {
  const random = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `material-ui-${random}`;
}
