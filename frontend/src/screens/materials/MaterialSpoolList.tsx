import { AlertTriangle, Boxes, CloudDownload, Plus } from "lucide-react";
import type { MaterialSpool, PrinterRecord } from "../../types";

type Props = {
  spools: MaterialSpool[];
  printers: PrinterRecord[];
  loading: boolean;
  syncing: boolean;
  syncPrinterId: number | null;
  onSyncPrinterChange: (printerId: number | null) => void;
  onSync: () => void;
  onCreate: () => void;
  onOpen: (spool: MaterialSpool) => void;
};

export function MaterialSpoolList(props: Props) {
  const { spools, printers, loading, syncing, syncPrinterId, onSyncPrinterChange, onSync, onCreate, onOpen } = props;
  return (
    <>
      <div className="panel-heading materials-heading">
        <div>
          <span className="materials-eyebrow">Materiais</span>
          <h2>Meus spools</h2>
          <p className="muted">Veja quanto material está disponível e o que precisa de atenção antes de preparar uma impressão.</p>
        </div>
        <button type="button" className="primary-button" onClick={onCreate}><Plus size={16} /> Adicionar spool</button>
      </div>

      <section className="materials-sync-card" aria-labelledby="spoolman-title">
        <CloudDownload size={22} />
        <div>
          <strong id="spoolman-title">Já usa o Spoolman?</strong>
          <span>O Printora consulta pelo agente da impressora. O inventário continua sendo alterado no Spoolman.</span>
        </div>
        <label>
          <span>Impressora</span>
          <select value={syncPrinterId ?? ""} onChange={(event) => onSyncPrinterChange(event.target.value ? Number(event.target.value) : null)}>
            <option value="">Selecione</option>
            {printers.map((printer) => <option key={printer.id} value={printer.id}>{printer.name}</option>)}
          </select>
        </label>
        <button type="button" className="secondary-button" onClick={onSync} disabled={!syncPrinterId || syncing}>
          {syncing ? "Sincronizando" : "Sincronizar"}
        </button>
      </section>

      {loading ? <div className="materials-empty" aria-live="polite">Carregando seus materiais.</div> : null}
      {!loading && spools.length === 0 ? (
        <section className="materials-empty">
          <Boxes size={34} />
          <h3>Nenhum spool cadastrado</h3>
          <p>Adicione o primeiro spool ou sincronize uma impressora que já usa o Spoolman.</p>
          <button type="button" className="primary-button" onClick={onCreate}>Adicionar meu primeiro spool</button>
        </section>
      ) : null}
      {!loading && spools.length > 0 ? (
        <section className="material-card-grid" aria-label="Spools disponíveis">
          {spools.map((spool) => {
            const percent = spool.initial_weight_g && spool.remaining_weight_g !== null
              ? Math.max(0, Math.min(100, (spool.remaining_weight_g / spool.initial_weight_g) * 100))
              : null;
            return (
              <button key={spool.id} type="button" className="material-card" onClick={() => onOpen(spool)}>
                <span className="material-color" style={{ background: spool.color_hex ?? "var(--surface-hover)" }} aria-hidden="true" />
                <span className="material-card-main">
                  <span className="material-card-title"><strong>{spool.name}</strong><small>{spool.source === "spoolman" ? "Sincronizado do Spoolman" : "Cadastrado no Printora"}</small></span>
                  <span>{[spool.material_type, spool.brand, spool.color_name].filter(Boolean).join(" · ")}</span>
                  <span className="material-weight"><strong>{formatWeight(spool.remaining_weight_g)}</strong><small>disponível</small></span>
                  {percent !== null ? <span className="material-weight-track" aria-label={`${Math.round(percent)}% do peso inicial`}><i style={{ width: `${percent}%` }} /></span> : null}
                  {spool.alerts.length > 0 ? <span className="material-warning"><AlertTriangle size={15} /> {spool.alerts.length} orientação(ões)</span> : <span className="material-ready">Sem alerta no cadastro</span>}
                </span>
              </button>
            );
          })}
        </section>
      ) : null}
    </>
  );
}

export function formatWeight(value: number | null) {
  if (value === null) return "Não informado";
  if (value >= 1000) return `${(value / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 2 })} kg`;
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} g`;
}
