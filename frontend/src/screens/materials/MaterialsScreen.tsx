import { useCallback, useEffect, useState } from "react";
import { materialsApi } from "../../services/materialsApi";
import { socialApi } from "../../services/socialApi";
import type { MaterialCompatibilityResult, MaterialConsumption, MaterialProfile, MaterialQualitySample, MaterialSpool, MaterialSpoolPayload } from "../../types";
import type { ScreenPropsFor } from "../ScreenProps";
import { MaterialSpoolDetail } from "./MaterialSpoolDetail";
import { MaterialSpoolForm } from "./MaterialSpoolForm";
import { MaterialSpoolList } from "./MaterialSpoolList";
import "../../styles/materials.css";

type Props = ScreenPropsFor<"printers" | "showToast" | "confirmAction">;
type Mode = "list" | "detail" | "create" | "edit";

export function MaterialsScreen({ printers, showToast, confirmAction }: Props) {
  const [mode, setMode] = useState<Mode>("list");
  const [spools, setSpools] = useState<MaterialSpool[]>([]);
  const [profiles, setProfiles] = useState<MaterialProfile[]>([]);
  const [selected, setSelected] = useState<MaterialSpool | null>(null);
  const [consumptions, setConsumptions] = useState<MaterialConsumption[]>([]);
  const [qualitySamples, setQualitySamples] = useState<MaterialQualitySample[]>([]);
  const [compatibility, setCompatibility] = useState<MaterialCompatibilityResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncPrinterId, setSyncPrinterId] = useState<number | null>(printers[0]?.id ?? null);

  const loadList = useCallback(async () => {
    setLoading(true);
    try {
      const [nextSpools, nextProfiles] = await Promise.all([materialsApi.spools(), socialApi.myMaterialProfiles()]);
      setSpools(nextSpools);
      setProfiles(nextProfiles);
    } catch (error) {
      showToast({ tone: "danger", title: "Não foi possível carregar os materiais", detail: errorMessage(error) });
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => { void loadList(); }, [loadList]);

  async function openSpool(spool: MaterialSpool) {
    setBusy(true);
    setCompatibility(null);
    try {
      const [freshSpool, nextConsumptions, nextQuality] = await Promise.all([
        materialsApi.spool(spool.id),
        materialsApi.consumptions(spool.id),
        materialsApi.quality(spool.id),
      ]);
      setSelected(freshSpool);
      setConsumptions(nextConsumptions);
      setQualitySamples(nextQuality);
      setMode("detail");
    } catch (error) {
      showToast({ tone: "danger", title: "Não foi possível abrir o spool", detail: errorMessage(error) });
    } finally {
      setBusy(false);
    }
  }

  async function saveSpool(payload: MaterialSpoolPayload & { revision?: number }) {
    setBusy(true);
    try {
      const saved = selected && mode === "edit"
        ? await materialsApi.updateSpool(selected.id, { ...payload, revision: payload.revision ?? selected.revision })
        : await materialsApi.createSpool(payload);
      await loadList();
      await openSpool(saved);
      showToast({ tone: "success", title: mode === "edit" ? "Spool atualizado" : "Spool adicionado", detail: "O material já está disponível para conferência." });
    } catch (error) {
      showToast({ tone: "danger", title: "Não foi possível salvar o spool", detail: errorMessage(error) });
    } finally {
      setBusy(false);
    }
  }

  async function archiveSelected() {
    if (!selected || selected.source !== "local") return;
    const confirmed = await confirmAction({
      tone: "warning",
      title: "Arquivar este spool?",
      detail: "Ele sai da lista de materiais disponíveis. O histórico de consumo e qualidade continua preservado.",
      evidence: selected.name,
      confirmLabel: "Arquivar spool",
    });
    if (!confirmed) return;
    setBusy(true);
    try {
      await materialsApi.archiveSpool(selected.id);
      setSelected(null);
      setMode("list");
      await loadList();
      showToast({ tone: "success", title: "Spool arquivado", detail: "O histórico foi preservado." });
    } catch (error) {
      showToast({ tone: "danger", title: "Não foi possível arquivar", detail: errorMessage(error) });
    } finally {
      setBusy(false);
    }
  }

  async function syncSpoolman() {
    if (!syncPrinterId) return;
    setSyncing(true);
    try {
      const result = await materialsApi.syncSpoolman(syncPrinterId);
      await loadList();
      showToast({
        tone: result.status === "synced" ? "success" : "warning",
        title: result.status === "synced" ? "Spoolman sincronizado" : "Spoolman indisponível",
        detail: result.status === "synced" ? `${result.total} spool(s) disponíveis. ${result.imported} novo(s).` : `${result.detail} Seus spools locais continuam disponíveis.`,
      });
    } catch (error) {
      showToast({ tone: "warning", title: "Spoolman indisponível", detail: `${errorMessage(error)} Seus spools locais continuam disponíveis.` });
    } finally {
      setSyncing(false);
    }
  }

  return (
    <article className="panel wide panel-section panel-materials">
      {mode === "list" ? <MaterialSpoolList spools={spools} printers={printers} loading={loading} syncing={syncing} syncPrinterId={syncPrinterId} onSyncPrinterChange={setSyncPrinterId} onSync={() => void syncSpoolman()} onCreate={() => { setSelected(null); setMode("create"); }} onOpen={(spool) => void openSpool(spool)} /> : null}
      {mode === "create" || mode === "edit" ? <MaterialSpoolForm key={`${mode}-${selected?.id ?? "new"}`} spool={mode === "edit" ? selected : null} profiles={profiles} saving={busy} onCancel={() => setMode(selected ? "detail" : "list")} onSave={saveSpool} /> : null}
      {mode === "detail" && selected ? (
        <MaterialSpoolDetail
          spool={selected}
          printers={printers}
          consumptions={consumptions}
          qualitySamples={qualitySamples}
          compatibility={compatibility}
          busy={busy}
          onBack={() => { setMode("list"); setSelected(null); }}
          onEdit={() => setMode("edit")}
          onArchive={archiveSelected}
          onCheckCompatibility={async (input) => {
            setBusy(true);
            try {
              setCompatibility(await materialsApi.compatibility({ spool_id: selected.id, material_profile_id: selected.material_profile_id, ...input }));
            } catch (error) {
              showToast({ tone: "danger", title: "Não foi possível conferir", detail: errorMessage(error) });
            } finally { setBusy(false); }
          }}
          onRecordConsumption={async (input) => {
            setBusy(true);
            try {
              await materialsApi.recordConsumption({ spool_id: selected.id, ...input });
              const [freshSpool, nextConsumptions] = await Promise.all([materialsApi.spool(selected.id), materialsApi.consumptions(selected.id)]);
              setSelected(freshSpool);
              setConsumptions(nextConsumptions);
              showToast({ tone: "success", title: "Uso registrado", detail: input.status === "confirmed" ? "O peso disponível foi atualizado uma única vez." : "A estimativa foi salva sem reduzir o peso disponível." });
            } catch (error) {
              showToast({ tone: "danger", title: "Não foi possível registrar o uso", detail: errorMessage(error) });
              throw error;
            } finally { setBusy(false); }
          }}
          onCreateQuality={async (input) => {
            setBusy(true);
            try {
              const sample = await materialsApi.createQuality({ spool_id: selected.id, ...input });
              setQualitySamples((current) => [sample, ...current]);
              showToast({ tone: sample.result === "passed" ? "success" : "warning", title: sample.result === "passed" ? "Medida dentro da tolerância" : "Medida fora da tolerância", detail: `Desvio calculado: ${sample.deviation_mm.toLocaleString("pt-BR")} mm.` });
            } catch (error) {
              showToast({ tone: "danger", title: "Não foi possível salvar a medição", detail: errorMessage(error) });
              throw error;
            } finally { setBusy(false); }
          }}
        />
      ) : null}
    </article>
  );
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Tente novamente em alguns instantes.";
}
