import type React from "react";
import type { AppSection } from "../../app/navigation";

export type SetLoading = React.Dispatch<React.SetStateAction<boolean>>;
export type SetError = React.Dispatch<React.SetStateAction<string | null>>;
export type SetActiveSection = React.Dispatch<React.SetStateAction<AppSection>>;

export function unknownErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Erro desconhecido";
}
