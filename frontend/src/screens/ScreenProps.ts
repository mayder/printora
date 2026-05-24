import type { PrintoraScreenProps } from "../hooks/usePrintoraApp";

export type ScreenPropsFor<Keys extends keyof PrintoraScreenProps> = Pick<PrintoraScreenProps, Keys>;
