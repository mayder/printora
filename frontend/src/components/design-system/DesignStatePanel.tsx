import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  CloudOff,
  Inbox,
  LoaderCircle,
  RefreshCw,
  Split,
} from "lucide-react";
import type { DesignState } from "../../types/designSystem";


const STATE_CONTENT: Record<
  DesignState,
  { title: string; detail: string; action: string; icon: typeof CheckCircle2 }
> = {
  loading: {
    title: "Carregando referência",
    detail: "Aguarde enquanto o contrato visual é consultado.",
    action: "Aguarde",
    icon: LoaderCircle,
  },
  empty: {
    title: "Nenhum item encontrado",
    detail: "Ajuste os filtros ou restaure a busca para continuar.",
    action: "Limpar filtros",
    icon: Inbox,
  },
  error: {
    title: "Não foi possível carregar",
    detail: "A tentativa falhou sem alterar seu rascunho.",
    action: "Tentar novamente",
    icon: AlertTriangle,
  },
  success: {
    title: "Referência pronta",
    detail: "O conteúdo atual pode ser revisado e testado.",
    action: "Continuar",
    icon: CheckCircle2,
  },
  partial: {
    title: "Conteúdo parcial",
    detail: "Parte da referência está disponível; confira a origem antes de decidir.",
    action: "Atualizar",
    icon: Split,
  },
  offline: {
    title: "Você está offline",
    detail: "O rascunho local permanece disponível. Reconecte para atualizar o catálogo.",
    action: "Verificar conexão",
    icon: CloudOff,
  },
  forbidden: {
    title: "Acesso não permitido",
    detail: "Sua sessão não possui acesso a esta referência.",
    action: "Voltar",
    icon: Ban,
  },
  conflict: {
    title: "Rascunho alterado em outra aba",
    detail: "Revise a versão mais recente antes de salvar novamente.",
    action: "Carregar versão atual",
    icon: RefreshCw,
  },
};

export function DesignStatePanel({
  state,
  onAction,
}: {
  state: DesignState;
  onAction?: () => void;
}) {
  const content = STATE_CONTENT[state];
  const Icon = content.icon;
  return (
    <section className={`ds-state ds-state-${state}`} aria-live={state === "loading" ? "polite" : "assertive"}>
      <Icon aria-hidden="true" className={state === "loading" ? "ds-spin" : undefined} />
      <div>
        <strong>{content.title}</strong>
        <p>{content.detail}</p>
      </div>
      {onAction ? (
        <button type="button" className="secondary-button" onClick={onAction} disabled={state === "loading"}>
          {content.action}
        </button>
      ) : null}
    </section>
  );
}
