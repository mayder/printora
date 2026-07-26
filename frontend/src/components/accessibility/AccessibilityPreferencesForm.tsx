import type {
  AccessibilityPreferenceValues,
  AccessibilityTheme,
  TactileFormat,
} from "../../types/accessibility";


type Props = {
  values: AccessibilityPreferenceValues;
  saving: boolean;
  offline: boolean;
  onChange: (patch: Partial<AccessibilityPreferenceValues>) => void;
  onSave: () => void;
};

export function AccessibilityPreferencesForm({
  values,
  saving,
  offline,
  onChange,
  onSave,
}: Props) {
  return (
    <form className="a11y-form" onSubmit={(event) => {
      event.preventDefault();
      onSave();
    }}>
      <fieldset>
        <legend>Visual e movimento</legend>
        <label>
          Tema adaptativo
          <select
            value={values.theme}
            onChange={(event) => onChange({ theme: event.target.value as AccessibilityTheme })}
          >
            <option value="system">Seguir sistema</option>
            <option value="light">Claro</option>
            <option value="dark">Escuro</option>
            <option value="high-contrast">Alto contraste</option>
          </select>
        </label>
        <label>
          Escala de texto: {values.text_scale_percent}%
          <input
            type="range"
            min="100"
            max="200"
            step="25"
            value={values.text_scale_percent}
            onChange={(event) => onChange({ text_scale_percent: Number(event.target.value) })}
          />
        </label>
        <Check
          checked={values.reduce_motion}
          label="Reduzir movimento e transições"
          onChange={(reduce_motion) => onChange({ reduce_motion })}
        />
      </fieldset>
      <fieldset>
        <legend>Navegação e leitor de tela</legend>
        <Check
          checked={values.keyboard_navigation}
          label="Destacar navegação por teclado e switch"
          onChange={(keyboard_navigation) => onChange({ keyboard_navigation })}
        />
        <Check
          checked={values.voice_navigation}
          label="Otimizar rótulos para navegação por voz"
          onChange={(voice_navigation) => onChange({ voice_navigation })}
        />
        <Check
          checked={values.screen_reader_announcements}
          label="Anunciar mudanças de estado ao leitor de tela"
          onChange={(screen_reader_announcements) => onChange({ screen_reader_announcements })}
        />
      </fieldset>
      <fieldset>
        <legend>Mídia e compreensão</legend>
        <Check
          checked={values.captions}
          label="Preferir legendas"
          onChange={(captions) => onChange({ captions })}
        />
        <Check
          checked={values.audio_descriptions}
          label="Preferir audiodescrição"
          onChange={(audio_descriptions) => onChange({ audio_descriptions })}
        />
        <Check
          checked={values.simple_language}
          label="Usar linguagem simples"
          onChange={(simple_language) => onChange({ simple_language })}
        />
        <Check
          checked={values.low_cognitive_load}
          label="Reduzir carga cognitiva e densidade"
          onChange={(low_cognitive_load) => onChange({ low_cognitive_load })}
        />
      </fieldset>
      <fieldset>
        <legend>Alternativas à visualização 3D</legend>
        <Check
          checked={values.three_d_text_alternative}
          label="Sempre mostrar alternativa textual"
          onChange={(three_d_text_alternative) => onChange({ three_d_text_alternative })}
        />
        <label>
          Formato tátil preferido
          <select
            value={values.tactile_format}
            onChange={(event) => onChange({ tactile_format: event.target.value as TactileFormat })}
          >
            <option value="svg">SVG em alto relevo</option>
            <option value="brf">BRF para braille</option>
          </select>
        </label>
      </fieldset>
      <div className="a11y-form-actions">
        <button className="primary-button" type="submit" disabled={saving || offline}>
          {saving ? "Sincronizando" : "Salvar preferências"}
        </button>
        {offline ? <span role="status">Offline: alterações preservadas nesta tela.</span> : null}
      </div>
    </form>
  );
}
function Check({
  checked,
  label,
  onChange,
}: {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="a11y-check">
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span>{label}</span>
    </label>
  );
}
