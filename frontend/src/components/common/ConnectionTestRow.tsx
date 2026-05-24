import type { ConnectionCheckResult } from "../../types";

export function ConnectionTestRow({
  label,
  result,
  emptyDetail,
}: {
  label: string;
  result?: ConnectionCheckResult | null;
  emptyDetail?: string;
}) {
  if (!result) {
    return (
      <div className="connection-test-row idle">
        <span>{label}</span>
        <strong>não testado</strong>
        <small>{emptyDetail ?? "Clique em testar conexões."}</small>
      </div>
    );
  }
  return (
    <div className={`connection-test-row ${result.ok ? "ok" : "failed"}`}>
      <span>{label}</span>
      <strong>{result.ok ? "OK" : "falhou"}</strong>
      <small>{result.target} · {result.detail}</small>
    </div>
  );
}
