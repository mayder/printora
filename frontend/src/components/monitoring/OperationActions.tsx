import { Box, Fan, Home, Move3D, SendHorizontal, ShieldCheck } from "lucide-react";
import { formatCapabilityStatus, formatOperationValue, numericValue } from "./formatters";
import { formatDateTime } from "../../utils/formatters";
import type {
  OperationAction,
  OperationActionExecutionAttempt,
  OperationActionPreview,
  OperationCapability,
  OperationStatusResponse,
} from "../../types";

type ActionParameters = Record<string, string | number>;

const moveSteps = {
  X: [-100, -10, -1, 1, 10, 100],
  Y: [-100, -10, -1, 1, 10, 100],
  Z: [-25, -1, -0.1, 0.1, 1, 25],
};

export function OperationActions({
  actions,
  capabilities,
  values,
  preview,
  executionAttempt,
  confirmationPhrase,
  loading,
  canSendCommands,
  operationStatus,
  onPreview,
  onPreflight,
  onExecute,
  onParameterChange,
  onPhraseChange,
  onValidateExecutionGate,
}: {
  actions: OperationAction[];
  capabilities: OperationCapability[];
  values: Record<string, Record<string, string>>;
  preview: OperationActionPreview | null;
  executionAttempt: OperationActionExecutionAttempt | null;
  confirmationPhrase: string;
  loading: boolean;
  canSendCommands: boolean;
  operationStatus: OperationStatusResponse | null;
  onPreview: (action: OperationAction, parameters?: ActionParameters) => void | Promise<void>;
  onPreflight: (action: OperationAction, parameters?: ActionParameters) => void | Promise<void>;
  onExecute: (action: OperationAction, parameters?: ActionParameters) => void | Promise<void>;
  onParameterChange: (actionId: string, parameterName: string, value: string) => void;
  onPhraseChange: (value: string) => void;
  onValidateExecutionGate: () => void | Promise<void>;
}) {
  function findAction(actionId: string) {
    return actions.find((action) => action.id === actionId) ?? null;
  }

  function capabilityFor(actionId: string) {
    return capabilities.find((capability) => capability.action_id === actionId);
  }

  function currentValue(actionId: string, parameterName: string, fallback: string | number) {
    return values[actionId]?.[parameterName] ?? String(fallback);
  }

  function updateValues(actionId: string, parameters: ActionParameters) {
    Object.entries(parameters).forEach(([name, value]) => onParameterChange(actionId, name, String(value)));
  }

  function requestPreview(actionId: string, parameters: ActionParameters = {}) {
    const action = findAction(actionId);
    if (!action) return;
    updateValues(actionId, parameters);
    void onPreview(action, parameters);
  }

  function requestPreflight(actionId: string, parameters: ActionParameters = {}) {
    const action = findAction(actionId);
    if (!action) return;
    updateValues(actionId, parameters);
    void onPreflight(action, parameters);
  }

  function requestExecute(actionId: string, parameters: ActionParameters = {}) {
    const action = findAction(actionId);
    if (!action) return;
    updateValues(actionId, parameters);
    void onExecute(action, parameters);
  }

  return (
    <div className="operation-actions-layout">
      {actions.length === 0 ? <p className="muted">Nenhuma ação operacional retornada pelo backend.</p> : null}

      <div className="operation-console-grid">
        <ToolheadPanel
          disabled={loading}
          status={operationStatus}
          moveXY={findAction("move_xy")}
          moveAbsolute={findAction("move_absolute")}
          moveZ={findAction("move_z")}
          home={findAction("home_xyz")}
          qgl={findAction("quad_gantry_level")}
          values={values}
          capabilityFor={capabilityFor}
          currentValue={currentValue}
          onChange={onParameterChange}
          onPreflight={requestPreflight}
          onExecute={requestExecute}
        />
        <ExtruderPanel
          disabled={loading}
          status={operationStatus}
          hotend={findAction("set_hotend_temp")}
          extrude={findAction("extrude")}
          pressureAdvance={findAction("set_pressure_advance")}
          values={values}
          capabilityFor={capabilityFor}
          currentValue={currentValue}
          onChange={onParameterChange}
          onExecute={requestExecute}
        />
        <MiscPanel
          disabled={loading}
          fan={findAction("set_fan")}
          led={findAction("set_led")}
          status={operationStatus}
          capabilityFor={capabilityFor}
          currentValue={currentValue}
          onChange={onParameterChange}
          onExecute={requestExecute}
        />
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
          <small>{formatDateTime(executionAttempt.created_at)}</small>
        </div>
      ) : null}

    </div>
  );
}

function ToolheadPanel({
  disabled,
  status,
  moveXY,
  moveAbsolute,
  moveZ,
  home,
  qgl,
  values,
  capabilityFor,
  currentValue,
  onChange,
  onPreflight,
  onExecute,
}: {
  disabled: boolean;
  status: OperationStatusResponse | null;
  moveXY: OperationAction | null;
  moveAbsolute: OperationAction | null;
  moveZ: OperationAction | null;
  home: OperationAction | null;
  qgl: OperationAction | null;
  values: Record<string, Record<string, string>>;
  capabilityFor: (actionId: string) => OperationCapability | undefined;
  currentValue: (actionId: string, parameterName: string, fallback: string | number) => string;
  onChange: (actionId: string, parameterName: string, value: string) => void;
  onPreflight: (actionId: string, parameters?: ActionParameters) => void;
  onExecute: (actionId: string, parameters?: ActionParameters) => void;
}) {
  const position = Array.isArray(status?.toolhead.position) ? status?.toolhead.position : [];
  const axisMinimum = Array.isArray(status?.toolhead.axis_minimum) ? status?.toolhead.axis_minimum : [];
  const axisMaximum = Array.isArray(status?.toolhead.axis_maximum) ? status?.toolhead.axis_maximum : [];
  const xyFeedrate = Number(currentValue("move_xy", "feedrate", 6000));
  const zFeedrate = Number(currentValue("move_z", "feedrate", 1200));

  return (
    <section className="operation-console-card toolhead">
      <PanelTitle icon={Move3D} title="Toolhead" detail="Home, QGL e movimento protegido" capability={capabilityFor("move_xy") ?? capabilityFor("home_xyz")} />
      <div className="operation-position-grid" aria-label="Posição atual">
        {["X", "Y", "Z"].map((axis, index) => (
          <PositionField
            key={axis}
            axis={axis}
            current={position[index]}
            minimum={axisMinimum[index]}
            maximum={axisMaximum[index]}
            value={currentValue(`move_absolute_${axis.toLowerCase()}`, "position_mm", position[index] ?? 0)}
            disabled={disabled || !moveAbsolute}
            onChange={(value) => onChange(`move_absolute_${axis.toLowerCase()}`, "position_mm", value)}
            onSubmit={(value) =>
              onExecute("move_absolute", {
                axis,
                position_mm: Number(value),
                feedrate: axis === "Z" ? zFeedrate : xyFeedrate,
              })
            }
          />
        ))}
      </div>
      <div className="operation-home-row">
        <button type="button" onClick={() => onExecute("home_xyz")} disabled={disabled || !home}>
          <Home size={14} />
          ALL
        </button>
        <button type="button" onClick={() => onExecute("quad_gantry_level")} disabled={disabled || !qgl}>
          QGL
        </button>
        <button type="button" disabled>
          Motores
        </button>
      </div>
      <div className="operation-jog-grid">
        {(["X", "Y"] as const).map((axis) => (
          <div key={axis} className="operation-jog-row">
            {moveSteps[axis].map((step) => (
              <button key={`${axis}-${step}`} type="button" disabled={disabled || !moveXY} onClick={() => onExecute("move_xy", { axis, distance_mm: step, feedrate: xyFeedrate })}>
                {step > 0 ? `+${step}` : step}
              </button>
            ))}
            <strong>{axis}</strong>
          </div>
        ))}
        <div className="operation-jog-row">
          {moveSteps.Z.map((step) => (
            <button key={`Z-${step}`} type="button" disabled={disabled || !moveZ} onClick={() => onExecute("move_z", { distance_mm: step, feedrate: zFeedrate })}>
              {step > 0 ? `+${step}` : step}
            </button>
          ))}
          <strong>Z</strong>
        </div>
      </div>
      <div className="operation-inline-fields two">
        <NumberField label="XY feedrate" value={currentValue("move_xy", "feedrate", 6000)} onChange={(value) => onChange("move_xy", "feedrate", value)} />
        <NumberField label="Z feedrate" value={currentValue("move_z", "feedrate", 1200)} onChange={(value) => onChange("move_z", "feedrate", value)} />
      </div>
      <MeterControl
        label="Speed factor"
        value={Number(currentValue("set_speed_factor", "speed_percent", numericValue(status?.toolhead.speed_factor) !== null ? Math.round(numericValue(status?.toolhead.speed_factor)! * 100) : 100))}
        unit="%"
        onChange={(value) => onChange("set_speed_factor", "speed_percent", String(value))}
        onSubmit={(value) => onExecute("set_speed_factor", { speed_percent: value })}
      />
    </section>
  );
}

function ExtruderPanel({
  disabled,
  status,
  hotend,
  extrude,
  pressureAdvance,
  capabilityFor,
  currentValue,
  onChange,
  onExecute,
}: {
  disabled: boolean;
  status: OperationStatusResponse | null;
  hotend: OperationAction | null;
  extrude: OperationAction | null;
  pressureAdvance: OperationAction | null;
  values: Record<string, Record<string, string>>;
  capabilityFor: (actionId: string) => OperationCapability | undefined;
  currentValue: (actionId: string, parameterName: string, fallback: string | number) => string;
  onChange: (actionId: string, parameterName: string, value: string) => void;
  onExecute: (actionId: string, parameters?: ActionParameters) => void;
}) {
  const length = Number(currentValue("extrude", "length_mm", 5));
  const feedrate = Number(currentValue("extrude", "feedrate", 300));
  const advance = currentValue("set_pressure_advance", "advance", numericValue(status?.extruder.pressure_advance) ?? 0);
  const smoothTime = currentValue("set_pressure_advance", "smooth_time", numericValue(status?.extruder.smooth_time) ?? 0.04);
  const submitPressureAdvance = () => onExecute("set_pressure_advance", { advance: Number(advance), smooth_time: Number(smoothTime) });

  return (
    <section className="operation-console-card extruder">
      <PanelTitle icon={Box} title="Extrusor" detail="Temperatura e filamento" capability={capabilityFor("extrude") ?? capabilityFor("set_pressure_advance") ?? capabilityFor("set_hotend_temp")} />
      <MeterControl
        label="Extrusion factor"
        value={Number(currentValue("set_extrusion_factor", "extrusion_percent", numericValue(status?.extruder.extrusion_factor) !== null ? Math.round(numericValue(status?.extruder.extrusion_factor)! * 100) : 100))}
        unit="%"
        onChange={(value) => onChange("set_extrusion_factor", "extrusion_percent", String(value))}
        onSubmit={(value) => onExecute("set_extrusion_factor", { extrusion_percent: value })}
      />
      <div className="operation-inline-fields two">
        <NumberField label="Pressure advance" value={advance} onChange={(value) => onChange("set_pressure_advance", "advance", value)} onEnter={submitPressureAdvance} />
        <NumberField label="Smooth time" value={smoothTime} unit="s" onChange={(value) => onChange("set_pressure_advance", "smooth_time", value)} onEnter={submitPressureAdvance} />
      </div>
      <div className="operation-button-row single">
        <button type="button" disabled={disabled || !pressureAdvance} onClick={submitPressureAdvance}>
          Enviar pressure advance
        </button>
      </div>
      <div className="operation-inline-fields two">
        <NumberField label="Filamento" value={String(length)} unit="mm" onChange={(value) => onChange("extrude", "length_mm", value)} />
        <NumberField label="Feedrate" value={String(feedrate)} unit="mm/s" onChange={(value) => onChange("extrude", "feedrate", value)} />
      </div>
      <div className="operation-button-row">
        <button type="button" disabled={disabled || !extrude} onClick={() => onExecute("extrude", { length_mm: -Math.abs(length), feedrate })}>
          Retrair
        </button>
        <button type="button" disabled={disabled || !extrude} onClick={() => onExecute("extrude", { length_mm: Math.abs(length), feedrate })}>
          Extrudar
        </button>
      </div>
      <div className="operation-inline-fields action">
        <NumberField label="Hotend alvo" value={currentValue("set_hotend_temp", "temperature", 0)} unit="°C" onChange={(value) => onChange("set_hotend_temp", "temperature", value)} />
        <button type="button" disabled={disabled || !hotend} onClick={() => onExecute("set_hotend_temp", { temperature: Number(currentValue("set_hotend_temp", "temperature", 0)) })}>
          Enviar
        </button>
      </div>
    </section>
  );
}

export function MachinePanel({
  disabled,
  status,
  setVelocityLimit,
  currentValue,
  onChange,
  onExecute,
}: {
  disabled: boolean;
  status: OperationStatusResponse | null;
  setVelocityLimit: OperationAction | null;
  currentValue: (actionId: string, parameterName: string, fallback: string | number) => string;
  onChange: (actionId: string, parameterName: string, value: string) => void;
  onExecute: (actionId: string, parameters?: ActionParameters) => void;
}) {
  const velocity = currentValue("set_velocity_limit", "velocity", numericValue(status?.toolhead.max_velocity) ?? 350);
  const accel = currentValue("set_velocity_limit", "accel", numericValue(status?.toolhead.max_accel) ?? 10000);
  const squareCornerVelocity = currentValue("set_velocity_limit", "square_corner_velocity", numericValue(status?.toolhead.square_corner_velocity) ?? 5);
  const submitLimits = () =>
    onExecute("set_velocity_limit", {
      velocity: Number(velocity),
      accel: Number(accel),
      square_corner_velocity: Number(squareCornerVelocity),
    });

  return (
    <section className="operation-console-card machine">
      <PanelTitle icon={ShieldCheck} title="Machine" detail="Limites atuais da impressora" />
      <div className="operation-inline-fields two">
        <NumberField label="Velocity" value={velocity} unit="mm/s" onChange={(value) => onChange("set_velocity_limit", "velocity", value)} onEnter={submitLimits} />
        <NumberField label="Acceleration" value={accel} unit="mm/s²" onChange={(value) => onChange("set_velocity_limit", "accel", value)} onEnter={submitLimits} />
      </div>
      <div className="operation-inline-fields two">
        <NumberField
          label="Square corner"
          value={squareCornerVelocity}
          unit="mm/s"
          onChange={(value) => onChange("set_velocity_limit", "square_corner_velocity", value)}
          onEnter={submitLimits}
        />
        <ReadOnlyField label="Home axes" value={formatOperationValue(status?.toolhead.homed_axes)} unit="" />
      </div>
      <div className="operation-button-row single">
        <button type="button" disabled={disabled || !setVelocityLimit} onClick={submitLimits}>
          Enviar limites
        </button>
      </div>
    </section>
  );
}

function MiscPanel({
  disabled,
  fan,
  led,
  status,
  capabilityFor,
  currentValue,
  onChange,
  onExecute,
}: {
  disabled: boolean;
  fan: OperationAction | null;
  led: OperationAction | null;
  status: OperationStatusResponse | null;
  capabilityFor: (actionId: string) => OperationCapability | undefined;
  currentValue: (actionId: string, parameterName: string, fallback: string | number) => string;
  onChange: (actionId: string, parameterName: string, value: string) => void;
  onExecute: (actionId: string, parameters?: ActionParameters) => void;
}) {
  const ledName = currentValue("set_led", "led_name", "");
  const ledBrightness = numericValue(currentValue("set_led", "brightness_percent", 0)) ?? 0;

  return (
    <section className="operation-console-card misc">
      <PanelTitle icon={Fan} title="Miscellaneous" detail="Fan e LED" capability={capabilityFor("set_fan") ?? capabilityFor("set_led")} />
      <div className="operation-misc-grid">
        {(status?.miscellaneous.fans ?? []).map((item) => {
          const fanKey = fanActionKey(item.object_name ?? item.name);
          const currentPercent = numericValue(item.speed) !== null ? Math.round(numericValue(item.speed)! * 100) : 0;
          const value = numericValue(currentValue(fanKey, "speed_percent", currentPercent)) ?? currentPercent;
          return (
            <div key={item.object_name ?? item.name} className="operation-fan-control">
              <div>
                <strong>{item.name}</strong>
                <span>RPM {item.rpm ?? "-"}</span>
              </div>
              <MeterControl
                label="Potência"
                value={value}
                unit="%"
                minimum={0}
                maximum={100}
                disabled={disabled || !fan}
                onChange={(nextValue) => onChange(fanKey, "speed_percent", String(nextValue))}
                onSubmit={(nextValue) => onExecute("set_fan", { fan_name: item.object_name ?? item.name, speed_percent: nextValue })}
              />
            </div>
          );
        })}
        {status?.miscellaneous.fans?.length ? null : <p className="muted operation-misc-wide">Nenhum fan retornado pelo Moonraker.</p>}
        <div className="operation-led-control">
          <TextField label="LED" value={ledName} onChange={(value) => onChange("set_led", "led_name", value)} />
          <MeterControl
            label="Brilho"
            value={ledBrightness}
            unit="%"
            minimum={0}
            maximum={100}
            disabled={disabled || !led}
            onChange={(nextValue) => onChange("set_led", "brightness_percent", String(nextValue))}
            onSubmit={(nextValue) => onExecute("set_led", { led_name: ledName, brightness_percent: nextValue })}
          />
        </div>
      </div>
    </section>
  );
}

function PositionField({
  axis,
  current,
  minimum,
  maximum,
  value,
  disabled,
  onChange,
  onSubmit,
}: {
  axis: string;
  current: unknown;
  minimum: unknown;
  maximum: unknown;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
}) {
  const limitText = typeof minimum === "number" && typeof maximum === "number" ? `${minimum} a ${maximum}` : "limite não informado";
  return (
    <label className="operation-position-field">
      <span>
        {axis}
        <small>Atual {formatOperationValue(current)}</small>
      </span>
      <span className="operation-console-input operation-position-input">
        <input
          inputMode="decimal"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") onSubmit(value);
          }}
        />
        <small>mm</small>
        <button type="button" disabled={disabled} onClick={() => onSubmit(value)} aria-label={`Enviar posição ${axis}`}>
          <SendHorizontal size={15} />
        </button>
      </span>
      <small>{limitText}</small>
    </label>
  );
}

function PanelTitle({
  icon: Icon,
  title,
  detail,
  capability,
}: {
  icon: typeof Move3D;
  title: string;
  detail: string;
  capability?: OperationCapability;
}) {
  return (
    <div className="operation-console-title">
      <Icon size={18} />
      <div>
        <strong>{title}</strong>
        <span>{detail}</span>
      </div>
      {capability ? <span className={`operation-action-status ${capability.status}`}>{formatCapabilityStatus(capability.status)}</span> : null}
    </div>
  );
}

function MeterControl({
  label,
  value,
  unit,
  minimum = 1,
  maximum = 300,
  stepSize = 5,
  disabled = false,
  onChange,
  onSubmit,
}: {
  label: string;
  value: number;
  unit: string;
  minimum?: number;
  maximum?: number;
  stepSize?: number;
  disabled?: boolean;
  onChange: (value: number) => void;
  onSubmit: (value: number) => void;
}) {
  const normalizedValue = Number.isFinite(value) ? value : minimum;
  const boundedValue = Math.max(minimum, Math.min(maximum, normalizedValue));
  const filledPercent = ((boundedValue - minimum) / (maximum - minimum)) * 100;
  function step(delta: number) {
    const nextValue = Math.max(minimum, Math.min(maximum, boundedValue + delta));
    onChange(nextValue);
    onSubmit(nextValue);
  }
  function submitRange(valueText: string) {
    const nextValue = Math.max(minimum, Math.min(maximum, Number(valueText)));
    onChange(nextValue);
    onSubmit(nextValue);
  }
  return (
    <div className="operation-meter-row operation-meter-control">
      <div>
        <span>{label}</span>
        <strong>
          {boundedValue} {unit}
        </strong>
      </div>
      <div className="operation-meter-control-row">
        <button type="button" disabled={disabled} onClick={() => step(-stepSize)} aria-label={`Diminuir ${label}`}>
          -
        </button>
        <input
          aria-label={label}
          className="operation-meter-slider"
          type="range"
          min={minimum}
          max={maximum}
          step="1"
          disabled={disabled}
          value={boundedValue}
          style={{ "--meter-fill": `${filledPercent}%` } as Record<string, string>}
          onChange={(event) => onChange(Number(event.target.value))}
          onMouseUp={(event) => submitRange(event.currentTarget.value)}
          onTouchEnd={(event) => submitRange(event.currentTarget.value)}
          onKeyUp={(event) => {
            if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End", "PageUp", "PageDown"].includes(event.key)) {
              submitRange(event.currentTarget.value);
            }
          }}
        />
        <button type="button" disabled={disabled} onClick={() => step(stepSize)} aria-label={`Aumentar ${label}`}>
          +
        </button>
      </div>
    </div>
  );
}

function ReadOnlyField({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <label className="operation-console-field readonly">
      <span>{label}</span>
      <strong>
        {value}
        {unit ? ` ${unit}` : ""}
      </strong>
    </label>
  );
}

function NumberField({ label, value, unit, onChange, onEnter }: { label: string; value: string; unit?: string; onChange: (value: string) => void; onEnter?: () => void }) {
  const compact = unit === "%" || unit === "°C";
  return (
    <label className={`operation-console-field ${compact ? "compact" : ""}`}>
      <span>{label}</span>
      <span className="operation-console-input">
        <input
          inputMode="decimal"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") onEnter?.();
          }}
        />
        {unit ? <small>{unit}</small> : null}
      </span>
    </label>
  );
}

function TextField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="operation-console-field">
      <span>{label}</span>
      <span className="operation-console-input">
        <input value={value} onChange={(event) => onChange(event.target.value)} />
      </span>
    </label>
  );
}

function fanActionKey(name: string) {
  return `set_fan_${name.replace(/[^a-zA-Z0-9_-]/g, "_")}`;
}
