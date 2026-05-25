import type React from "react";
import type { AppSection } from "../../app/navigation";

export type SetLoading = React.Dispatch<React.SetStateAction<boolean>>;
export type SetError = React.Dispatch<React.SetStateAction<string | null>>;
export type SetActiveSection = React.Dispatch<React.SetStateAction<AppSection>>;

export function unknownErrorMessage(error: unknown) {
  if (error instanceof TypeError && error.message === "Failed to fetch") {
    return "API do Printora indisponível. Abra pelo launcher ou verifique se o backend está rodando em http://127.0.0.1:8069.";
  }
  return error instanceof Error ? error.message : "Erro desconhecido";
}
