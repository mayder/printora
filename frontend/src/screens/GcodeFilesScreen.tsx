import React from "react";
import { Database, FileText, Folder, HardDrive, Image, RefreshCw, Search, Square, SquareCheckBig } from "lucide-react";
import { operationApi } from "../services/operationApi";
import type { GcodeFilesResponse, OperationGcodeFile } from "../types";
import type { PrintoraScreenProps } from "../hooks/usePrintoraApp";

type SortKey = "modified" | "name" | "size" | "estimated_time" | "slicer";
type MetadataFilter = "all" | "with_metadata" | "without_metadata";

export function GcodeFilesScreen({ selectedPrinter, selectedPrinterId, showToast }: PrintoraScreenProps) {
  const [payload, setPayload] = React.useState<GcodeFilesResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [directory, setDirectory] = React.useState("all");
  const [metadataFilter, setMetadataFilter] = React.useState<MetadataFilter>("all");
  const [sortKey, setSortKey] = React.useState<SortKey>("modified");
  const [selection, setSelection] = React.useState<Set<string>>(() => new Set());

  const loadFiles = React.useCallback(
    async (refresh = false) => {
      if (!selectedPrinterId) return;
      setLoading(true);
      try {
        const result = await operationApi.gcodeFiles(selectedPrinterId, { refresh, limit: 500 });
        setPayload(result);
        setSelection(new Set());
        if (result.data_state === "offline" || result.data_state === "error" || result.data_state === "unsupported") {
          showToast({ tone: "warning", title: "Arquivos G-code indisponíveis", detail: result.error || result.summary });
        }
      } catch (err) {
        const detail = err instanceof Error ? err.message : "Falha ao carregar arquivos G-code";
        setPayload(null);
        showToast({ tone: "danger", title: "Falha ao carregar G-code", detail });
      } finally {
        setLoading(false);
      }
    },
    [selectedPrinterId, showToast],
  );

  React.useEffect(() => {
    void loadFiles(false);
  }, [loadFiles]);

  const files = React.useMemo(
    () => filterAndSortFiles(payload?.files ?? [], query, directory, metadataFilter, sortKey),
    [directory, metadataFilter, payload?.files, query, sortKey],
  );
  const directories = payload?.directories ?? [];
  const selectedCount = files.filter((file) => selection.has(file.path ?? file.filename)).length;
  const allVisibleSelected = files.length > 0 && selectedCount === files.length;

  function toggleAllVisible() {
    setSelection((current) => {
      const next = new Set(current);
      if (allVisibleSelected) {
        files.forEach((file) => next.delete(file.path ?? file.filename));
      } else {
        files.forEach((file) => next.add(file.path ?? file.filename));
      }
      return next;
    });
  }

  function toggleFile(file: OperationGcodeFile) {
    const key = file.path ?? file.filename;
    setSelection((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  if (!selectedPrinter || !selectedPrinterId) {
    return (
      <article className="panel wide panel-section gcode-files-screen">
        <EmptyState title="Nenhuma impressora aberta" detail="Abra uma impressora para consultar os G-codes do Moonraker." />
      </article>
    );
  }

  return (
    <article className="panel wide panel-section gcode-files-screen">
      <div className="gcode-files-topbar">
        <div>
          <h2>Arquivos G-code</h2>
          <p className="muted">{payload?.summary ?? `Arquivos de ${selectedPrinter.name}`}</p>
        </div>
        <button type="button" className="secondary-button" onClick={() => void loadFiles(true)} disabled={loading}>
          <RefreshCw className={loading ? "button-busy-icon" : undefined} size={15} />
          Atualizar
        </button>
      </div>

      <div className="gcode-files-metrics">
        <Metric icon={FileText} label="Arquivos" value={String(payload?.files.length ?? 0)} />
        <Metric icon={Folder} label="Pastas" value={String(directories.length)} />
        <Metric icon={SquareCheckBig} label="Selecionados" value={String(selectedCount)} />
        <Metric icon={HardDrive} label="Livre" value={formatBytes(payload?.storage?.free)} detail={formatStorageDetail(payload)} />
      </div>

      <div className="gcode-files-controls">
        <label className="gcode-search-field">
          <Search size={15} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar arquivo, pasta, material ou slicer" />
        </label>
        <select aria-label="Filtrar pasta" value={directory} onChange={(event) => setDirectory(event.target.value)}>
          <option value="all">Todas as pastas</option>
          {directories.map((item) => (
            <option key={item.path} value={item.path}>
              {item.path}
            </option>
          ))}
        </select>
        <select aria-label="Filtrar metadados" value={metadataFilter} onChange={(event) => setMetadataFilter(event.target.value as MetadataFilter)}>
          <option value="all">Todos</option>
          <option value="with_metadata">Com metadados</option>
          <option value="without_metadata">Sem metadados</option>
        </select>
        <select aria-label="Ordenar arquivos" value={sortKey} onChange={(event) => setSortKey(event.target.value as SortKey)}>
          <option value="modified">Atualização</option>
          <option value="name">Nome</option>
          <option value="size">Tamanho</option>
          <option value="estimated_time">Tempo</option>
          <option value="slicer">Slicer</option>
        </select>
      </div>

      {payload?.data_state === "offline" || payload?.data_state === "error" || payload?.data_state === "unsupported" ? (
        <div className="monitor-note gcode-files-state">
          <Database size={17} />
          <span>{payload.error || payload.summary}</span>
        </div>
      ) : null}

      {loading && !payload ? <EmptyState title="Carregando arquivos" detail="Consultando a lista atual do agente." /> : null}
      {!loading && payload && files.length === 0 ? <EmptyState title="Nenhum G-code encontrado" detail="Ajuste a busca ou atualize a leitura do Moonraker." /> : null}

      {files.length ? (
        <div className="gcode-files-table-wrap">
          <table className="gcode-files-full-table">
            <thead>
              <tr>
                <th>
                  <button type="button" className="icon-button" onClick={toggleAllVisible} aria-label={allVisibleSelected ? "Limpar seleção" : "Selecionar arquivos visíveis"}>
                    {allVisibleSelected ? <SquareCheckBig size={15} /> : <Square size={15} />}
                  </button>
                </th>
                <th>Arquivo</th>
                <th>Atualizado</th>
                <th>Tamanho</th>
                <th>Objeto</th>
                <th>Camada</th>
                <th>Bico</th>
                <th>Filamento</th>
                <th>Tempo</th>
                <th>Temperaturas</th>
                <th>Slicer</th>
                <th>Última impressão</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => {
                const key = file.path ?? file.filename;
                return (
                  <tr key={key} className={selection.has(key) ? "is-selected" : ""}>
                    <td>
                      <button type="button" className="icon-button" onClick={() => toggleFile(file)} aria-label={selection.has(key) ? `Remover ${file.name ?? file.filename} da seleção` : `Selecionar ${file.name ?? file.filename}`}>
                        {selection.has(key) ? <SquareCheckBig size={15} /> : <Square size={15} />}
                      </button>
                    </td>
                    <td>
                      <div className="gcode-file-name-cell">
                        <Thumbnail file={file} />
                        <div>
                          <strong title={key}>{file.name || displayGcodeFileName(file.filename)}</strong>
                          <span title={key}>{file.directory || "raiz"}</span>
                        </div>
                      </div>
                    </td>
                    <td>{formatUnixDate(file.modified)}</td>
                    <td>{formatBytes(file.size)}</td>
                    <td>{formatMillimeters(file.object_height)}</td>
                    <td>{formatLayer(file)}</td>
                    <td>{formatMillimeters(file.nozzle_diameter)}</td>
                    <td>{formatGcodeFileFilament(file)}</td>
                    <td>{formatDuration(file.estimated_time)}</td>
                    <td>{formatTemperatures(file)}</td>
                    <td>{formatSlicer(file.slicer, file.slicer_version)}</td>
                    <td>{formatLastPrint(file)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </article>
  );
}

function Metric({ icon: Icon, label, value, detail }: { icon: React.ComponentType<{ size?: number }>; label: string; value: string; detail?: string }) {
  return (
    <div className="gcode-files-metric">
      <Icon size={17} />
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}

function Thumbnail({ file }: { file: OperationGcodeFile }) {
  const thumbnail = file.thumbnail;
  if (thumbnail?.data_uri) {
    return <img src={thumbnail.data_uri} alt="" className="gcode-file-thumbnail" loading="lazy" />;
  }
  return (
    <span className="gcode-file-thumbnail gcode-file-thumbnail-fallback" aria-hidden="true">
      <Image size={17} />
    </span>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="gcode-files-empty-state">
      <Database size={20} />
      <div>
        <strong>{title}</strong>
        <span>{detail}</span>
      </div>
    </div>
  );
}

function filterAndSortFiles(files: OperationGcodeFile[], query: string, directory: string, metadataFilter: MetadataFilter, sortKey: SortKey) {
  const needle = query.trim().toLowerCase();
  return files
    .filter((file) => {
      const key = file.path ?? file.filename;
      if (directory !== "all" && file.directory !== directory) return false;
      if (metadataFilter === "with_metadata" && !file.metadata_available) return false;
      if (metadataFilter === "without_metadata" && file.metadata_available) return false;
      if (!needle) return true;
      return [file.filename, key, file.directory, file.slicer, file.slicer_version, file.filament_type, file.filament_name]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle));
    })
    .sort((left, right) => compareFiles(left, right, sortKey));
}

function compareFiles(left: OperationGcodeFile, right: OperationGcodeFile, sortKey: SortKey) {
  if (sortKey === "name") return (left.name ?? left.filename).localeCompare(right.name ?? right.filename, "pt-BR");
  if (sortKey === "slicer") return formatSlicer(left.slicer, left.slicer_version).localeCompare(formatSlicer(right.slicer, right.slicer_version), "pt-BR");
  return numericValue(right[sortKey]) - numericValue(left[sortKey]);
}

function numericValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : -1;
}

function displayGcodeFileName(filename?: string | null) {
  const clean = (filename ?? "").trim();
  if (!clean) return "-";
  return clean.split("/").filter(Boolean).pop() ?? clean;
}

function formatUnixDate(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) return "-";
  const timestamp = value > 1000000000000 ? value : value * 1000;
  return new Date(timestamp).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function formatBytes(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) return "-";
  if (value < 1024) return `${Math.round(value)} B`;
  const units = ["KB", "MB", "GB"];
  let size = value / 1024;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size >= 10 ? size.toFixed(1) : size.toFixed(2)} ${units[unitIndex]}`;
}

function formatStorageDetail(payload: GcodeFilesResponse | null) {
  const used = formatBytes(payload?.storage?.used);
  const total = formatBytes(payload?.storage?.total);
  return used !== "-" || total !== "-" ? `${used} usado(s) de ${total}` : "";
}

function formatMillimeters(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) return "-";
  return `${value >= 10 ? value.toFixed(1) : value.toFixed(2)} mm`;
}

function formatLayer(file: OperationGcodeFile) {
  const height = formatMillimeters(file.layer_height);
  if (typeof file.layer_count === "number" && Number.isFinite(file.layer_count)) return `${file.layer_count} · ${height}`;
  return height;
}

function formatGcodeFileFilament(file: OperationGcodeFile) {
  const material = file.filament_type || file.filament_name || "";
  const weight = typeof file.filament_weight_total === "number" ? `${file.filament_weight_total.toFixed(1)} g` : "";
  const length = typeof file.filament_total === "number" ? `${Math.round(file.filament_total)} mm` : "";
  return [material, weight || length].filter(Boolean).join(" · ") || "-";
}

function formatDuration(seconds?: number | null) {
  if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds <= 0) return "-";
  const totalSeconds = Math.round(seconds);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const remainingSeconds = totalSeconds % 60;
  if (hours > 0) return `${hours}h ${String(minutes).padStart(2, "0")}m`;
  return `${minutes}m ${String(remainingSeconds).padStart(2, "0")}s`;
}

function formatTemperatures(file: OperationGcodeFile) {
  const extruder = typeof file.first_layer_extr_temp === "number" ? `${Math.round(file.first_layer_extr_temp)}C` : "";
  const bed = typeof file.first_layer_bed_temp === "number" ? `${Math.round(file.first_layer_bed_temp)}C mesa` : "";
  return [extruder, bed].filter(Boolean).join(" · ") || "-";
}

function formatSlicer(slicer?: string | null, version?: string | null) {
  if (!slicer && !version) return "-";
  return [slicer, version].filter(Boolean).join(" ");
}

function formatLastPrint(file: OperationGcodeFile) {
  const duration = formatDuration(file.last_print_duration);
  const end = formatUnixDate(file.print_end_time ?? file.print_start_time);
  if (duration === "-" && end === "-") return "-";
  return [duration, end].filter((item) => item !== "-").join(" · ");
}
