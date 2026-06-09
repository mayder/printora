import type React from "react";
import type { AppSection } from "../../app/navigation";

export type SetLoading = React.Dispatch<React.SetStateAction<boolean>>;
export type SetError = React.Dispatch<React.SetStateAction<string | null>>;
export type SetActiveSection = React.Dispatch<React.SetStateAction<AppSection>>;

export function unknownErrorMessage(error: unknown) {
  if (error instanceof TypeError && error.message === "Failed to fetch") {
    return "API do Printora indisponível. Abra pelo launcher ou verifique se o backend está rodando em http://127.0.0.1:8069.";
  }
  if (!(error instanceof Error)) {
    return "Erro desconhecido";
  }
  return friendlyErrorMessage(error.message);
}

function friendlyErrorMessage(message: string) {
  const detail = normalizeReadableError(parseErrorDetail(message));
  if (detail === "autenticação reforçada obrigatória para ação crítica") {
    return "Ação crítica bloqueada. Gere uma autorização em Conta > 2FA e autenticação reforçada e tente novamente.";
  }
  if (detail === "api route not found") {
    return "Rota da API não encontrada. Atualize a página e confirme se backend e frontend estão na mesma versão.";
  }
  return detail;
}

function normalizeReadableError(message: string) {
  const compact = message.replace(/\s+/g, " ").trim();
  const lower = compact.toLowerCase();
  if (
    lower.includes("error 524") ||
    lower.includes("cloudflare") ||
    lower.includes("cf-error") ||
    lower.includes("<!doctype") ||
    lower.includes("<html")
  ) {
    return "A requisição demorou mais que o limite do gateway. A impressora pode continuar executando; confira o histórico e o console antes de repetir.";
  }
  if (compact.length > 500) {
    return `${compact.slice(0, 497)}...`;
  }
  return compact;
}

function parseErrorDetail(message: string) {
  try {
    const payload = JSON.parse(message) as { detail?: unknown; message?: unknown };
    if (typeof payload.detail === "string") return payload.detail;
    if (typeof payload.message === "string") return payload.message;
  } catch {
    // Mensagem já está em texto legível.
  }
  return message;
}
