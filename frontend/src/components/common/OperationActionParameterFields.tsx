import type { OperationAction } from "../../types";
import { formatOperationParameterLabel, operationActionParameterSpecs } from "../../utils/formatters";

export function OperationActionParameterFields({
  action,
  values,
  onChange,
}: {
  action: OperationAction;
  values: Record<string, string>;
  onChange: (actionId: string, parameterName: string, value: string) => void;
}) {
  const parameters = operationActionParameterSpecs(action.id);
  if (parameters.length === 0) {
    return <small className="operation-action-no-params">Sem parâmetros.</small>;
  }
  return (
    <div className="operation-action-params">
      {parameters.map((parameter) => (
        <label key={`${action.id}-${parameter.name}`}>
          <span>{formatOperationParameterLabel(parameter.name)}</span>
          {parameter.type === "enum" ? (
            <select
              value={values[parameter.name] ?? String(parameter.default ?? parameter.values?.[0] ?? "")}
              onChange={(event) => onChange(action.id, parameter.name, event.target.value)}
            >
              {(parameter.values ?? []).map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={parameter.type === "number" ? "number" : "text"}
              min={parameter.min}
              max={parameter.max}
              value={values[parameter.name] ?? String(parameter.default ?? 0)}
              onChange={(event) => onChange(action.id, parameter.name, event.target.value)}
            />
          )}
        </label>
      ))}
    </div>
  );
}
