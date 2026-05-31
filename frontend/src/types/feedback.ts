export type FeedbackTone = "info" | "success" | "warning" | "danger";

export type ToastRecord = {
  id: number;
  tone: FeedbackTone;
  title: string;
  detail?: string;
  actionLabel?: string;
  onAction?: () => void | Promise<void>;
};

export type ConfirmDialogState = {
  open: boolean;
  tone: FeedbackTone;
  title: string;
  detail: string;
  evidence?: string;
  confirmLabel: string;
  cancelLabel: string;
};

export type ConfirmActionOptions = {
  tone?: FeedbackTone;
  title: string;
  detail: string;
  evidence?: string;
  confirmLabel?: string;
  cancelLabel?: string;
};

export type ShowToastOptions = {
  tone?: FeedbackTone;
  title: string;
  detail?: string;
  actionLabel?: string;
  onAction?: () => void | Promise<void>;
};
