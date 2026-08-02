import { ArrowLeft, Save } from "lucide-react";
import { useState } from "react";
import type { MaterialProfile, MaterialSpool, MaterialSpoolPayload, MaterialStorageState } from "../../types";

type Props = {
  spool: MaterialSpool | null;
  profiles: MaterialProfile[];
  saving: boolean;
  onCancel: () => void;
  onSave: (payload: MaterialSpoolPayload & { revision?: number }) => Promise<void>;
};

export function MaterialSpoolForm({ spool, profiles, saving, onCancel, onSave }: Props) {
  const [name, setName] = useState(spool?.name ?? "");
  const [materialType, setMaterialType] = useState(spool?.material_type ?? "PLA");
  const [brand, setBrand] = useState(spool?.brand ?? "");
  const [colorName, setColorName] = useState(spool?.color_name ?? "");
  const [colorHex, setColorHex] = useState(spool?.color_hex ?? "");
  const [lotCode, setLotCode] = useState(spool?.lot_code ?? "");
  const [initialWeight, setInitialWeight] = useState(numberInput(spool?.initial_weight_g));
  const [remainingWeight, setRemainingWeight] = useState(numberInput(spool?.remaining_weight_g));
  const [location, setLocation] = useState(spool?.location ?? "");
  const [storageState, setStorageState] = useState<MaterialStorageState>(spool?.storage_state ?? "unknown");
  const [profileId, setProfileId] = useState(spool?.material_profile_id?.toString() ?? "");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    await onSave({
      name,
      material_type: materialType,
      brand,
      color_name: colorName,
      color_hex: colorHex || null,
      lot_code: lotCode,
      initial_weight_g: parseOptionalNumber(initialWeight),
      remaining_weight_g: parseOptionalNumber(remainingWeight),
      location,
      storage_state: storageState,
      material_profile_id: profileId ? Number(profileId) : null,
      revision: spool?.revision,
    });
  }

  return (
    <form className="material-form" onSubmit={(event) => void submit(event)}>
      <div className="panel-heading materials-heading">
        <div>
          <button type="button" className="text-button material-back" onClick={onCancel}><ArrowLeft size={16} /> Voltar</button>
          <h2>{spool ? "Editar spool" : "Adicionar spool"}</h2>
          <p className="muted">Preencha o que você sabe. Campos sem informação permanecem como não confirmados.</p>
        </div>
      </div>

      <section className="material-form-section">
        <h3>Identificação</h3>
        <div className="material-form-grid">
          <label><span>Nome do spool *</span><input required minLength={2} value={name} onChange={(event) => setName(event.target.value)} placeholder="Ex.: PLA Branco" /></label>
          <label><span>Tipo do material *</span><input required minLength={2} value={materialType} onChange={(event) => setMaterialType(event.target.value)} placeholder="Ex.: PLA, PETG, ABS" /></label>
          <label><span>Marca</span><input value={brand} onChange={(event) => setBrand(event.target.value)} /></label>
          <label><span>Cor</span><input value={colorName} onChange={(event) => setColorName(event.target.value)} placeholder="Ex.: Branco neve" /></label>
          <label><span>Cor visual</span><input type="color" value={colorHex || "#777777"} onChange={(event) => setColorHex(event.target.value)} /></label>
          <label><span>Lote</span><input value={lotCode} onChange={(event) => setLotCode(event.target.value)} /></label>
        </div>
      </section>

      <section className="material-form-section">
        <h3>Peso e localização</h3>
        <div className="material-form-grid">
          <label><span>Peso inicial (g)</span><input type="number" min="0" step="0.1" value={initialWeight} onChange={(event) => setInitialWeight(event.target.value)} /></label>
          <label><span>Peso disponível (g)</span><input type="number" min="0" step="0.1" value={remainingWeight} onChange={(event) => setRemainingWeight(event.target.value)} /></label>
          <label><span>Onde está guardado?</span><input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Ex.: Caixa seca 1" /></label>
          <label><span>Como está armazenado?</span><select value={storageState} onChange={(event) => setStorageState(event.target.value as MaterialStorageState)}><option value="unknown">Não sei informar</option><option value="sealed">Lacrado</option><option value="open">Aberto</option><option value="drying">Em secagem</option><option value="dry">Seco e protegido</option></select></label>
        </div>
      </section>

      <details className="material-form-section">
        <summary>Vincular a um perfil técnico</summary>
        <p className="muted">O vínculo ajuda a comparar material e impressora. Ele não aplica configurações automaticamente.</p>
        <label><span>Perfil de material</span><select value={profileId} onChange={(event) => setProfileId(event.target.value)}><option value="">Sem perfil confirmado</option>{profiles.map((profile) => <option key={profile.id} value={profile.id}>{profile.title} · {profile.material_type}</option>)}</select></label>
      </details>

      <div className="material-form-actions"><button type="button" className="secondary-button" onClick={onCancel}>Cancelar</button><button type="submit" className="primary-button" disabled={saving}><Save size={16} /> {saving ? "Salvando" : "Salvar spool"}</button></div>
    </form>
  );
}

function numberInput(value: number | null | undefined) {
  return value === null || value === undefined ? "" : String(value);
}

function parseOptionalNumber(value: string) {
  return value.trim() ? Number(value) : null;
}
