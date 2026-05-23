import React from "react";
import { maintenanceApi } from "../../services/maintenanceApi";
import type { MaintenanceEventRecord, MaintenancePrintHoursStatus, MaintenanceSummary, MaintenanceTaskRecord } from "../../types";
import { formatMaintenanceIntervalValue } from "../../utils/formatters";
import type { SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UseMaintenanceOptions = {
  selectedPrinterId: number | null;
  setError: SetError;
  setLoading: SetLoading;
};

export function useMaintenance({ selectedPrinterId, setError, setLoading }: UseMaintenanceOptions) {
  const [maintenanceEvents, setMaintenanceEvents] = React.useState<MaintenanceEventRecord[]>([]);
  const [maintenanceTasks, setMaintenanceTasks] = React.useState<MaintenanceTaskRecord[]>([]);
  const [maintenanceSummary, setMaintenanceSummary] = React.useState<MaintenanceSummary | null>(null);
  const [maintenancePrintHours, setMaintenancePrintHours] = React.useState<MaintenancePrintHoursStatus | null>(null);
  const [maintenanceFilter, setMaintenanceFilter] = React.useState<"all" | "due" | "soon" | "ok">("all");
  const [maintenanceEventType, setMaintenanceEventType] = React.useState<MaintenanceEventRecord["event_type"] | "">("");
  const [maintenanceComponent, setMaintenanceComponent] = React.useState("");
  const [maintenanceTitle, setMaintenanceTitle] = React.useState("");
  const [maintenanceNotes, setMaintenanceNotes] = React.useState("");
  const [maintenanceDoneTask, setMaintenanceDoneTask] = React.useState<MaintenanceTaskRecord | null>(null);
  const [maintenanceDoneNotes, setMaintenanceDoneNotes] = React.useState("");
  const [maintenanceDoneIntervalKind, setMaintenanceDoneIntervalKind] = React.useState<"days" | "print_hours">("days");
  const [maintenanceDoneIntervalValue, setMaintenanceDoneIntervalValue] = React.useState("");
  const [maintenanceDoneDisableReminder, setMaintenanceDoneDisableReminder] = React.useState(false);
  const [maintenanceFreeModalOpen, setMaintenanceFreeModalOpen] = React.useState(false);
  const [maintenanceFreeReminderEnabled, setMaintenanceFreeReminderEnabled] = React.useState(false);
  const [maintenanceFreeIntervalKind, setMaintenanceFreeIntervalKind] = React.useState<"days" | "print_hours">("days");
  const [maintenanceFreeIntervalValue, setMaintenanceFreeIntervalValue] = React.useState("");

  async function loadMaintenance(printerId: number, refreshPrintHours = true) {
    const [eventsResponse, tasksResponse, summaryResponse] = await Promise.all([
      maintenanceApi.events(printerId),
      maintenanceApi.tasks(printerId),
      maintenanceApi.summary(printerId),
    ]);
    let loadedTasks: MaintenanceTaskRecord[] | null = null;
    let loadedSummary: MaintenanceSummary | null = null;
    if (eventsResponse.ok) {
      const payload = (await eventsResponse.json()) as { events: MaintenanceEventRecord[] };
      setMaintenanceEvents(payload.events);
    }
    if (tasksResponse.ok) {
      const payload = (await tasksResponse.json()) as { tasks: MaintenanceTaskRecord[] };
      loadedTasks = payload.tasks;
      setMaintenanceTasks(payload.tasks);
    }
    if (summaryResponse.ok) {
      loadedSummary = (await summaryResponse.json()) as MaintenanceSummary;
      setMaintenanceSummary(loadedSummary);
    }
    if (loadedTasks?.length === 0 && loadedSummary && loadedSummary.recommended_tasks.length > 0) {
      const response = await maintenanceApi.createDefaults(printerId);
      if (response.ok) {
        await loadMaintenance(printerId);
      }
    }
    if (refreshPrintHours) {
      void maintenanceApi.printHours(printerId)
        .then(async (response) => {
          if (!response.ok) {
            setMaintenancePrintHours({ available: false, total_print_hours: null, source: "unavailable" });
            return undefined;
          }
          const payload = (await response.json()) as MaintenancePrintHoursStatus;
          setMaintenancePrintHours(payload);
          return loadMaintenance(printerId, false);
        })
        .catch(() => setMaintenancePrintHours({ available: false, total_print_hours: null, source: "unavailable" }));
    }
  }

  function openMaintenanceDoneModal(task: MaintenanceTaskRecord) {
    setMaintenanceDoneTask(task);
    setMaintenanceDoneNotes("");
    setMaintenanceDoneIntervalKind(task.interval_kind);
    setMaintenanceDoneIntervalValue(task.is_active ? formatMaintenanceIntervalValue(task) : "");
    setMaintenanceDoneDisableReminder(!task.is_active);
  }

  function openMaintenanceFreeModal() {
    setMaintenanceEventType("");
    setMaintenanceComponent("");
    setMaintenanceTitle("");
    setMaintenanceNotes("");
    setMaintenanceFreeReminderEnabled(false);
    setMaintenanceFreeIntervalKind("days");
    setMaintenanceFreeIntervalValue("");
    setMaintenanceFreeModalOpen(true);
  }

  async function completeMaintenanceTask(
    taskId: number,
    notes = "Concluído pelo painel Printora.",
    nextIntervalKind?: "days" | "print_hours" | null,
    nextIntervalValue?: number | null,
    disableReminder = false,
  ): Promise<boolean> {
    if (!selectedPrinterId) {
      return false;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await maintenanceApi.completeTask(taskId, {
        notes,
        next_interval_kind: nextIntervalKind ?? null,
        next_interval_value: nextIntervalValue ?? null,
        next_interval_days: nextIntervalKind === "days" ? nextIntervalValue ?? null : null,
        disable_reminder: disableReminder,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
      return true;
    } catch (err) {
      setError(unknownErrorMessage(err));
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function submitMaintenanceDone(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!maintenanceDoneTask) {
      return;
    }
    const interval = maintenanceDoneDisableReminder || !maintenanceDoneIntervalValue.trim()
      ? null
      : Number(maintenanceDoneIntervalValue);
    if (!maintenanceDoneDisableReminder && maintenanceDoneIntervalKind === "print_hours" && !maintenancePrintHours?.available) {
      setError("Horas de impressão indisponíveis. Ligue a impressora para usar lembrete por horas.");
      return;
    }
    const completed = await completeMaintenanceTask(
      maintenanceDoneTask.id,
      maintenanceDoneNotes.trim() || "Manutenção realizada.",
      maintenanceDoneDisableReminder || interval === null ? null : maintenanceDoneIntervalKind,
      interval,
      maintenanceDoneDisableReminder || !maintenanceDoneIntervalValue.trim(),
    );
    if (!completed) {
      return;
    }
    setMaintenanceDoneTask(null);
    setMaintenanceDoneNotes("");
    setMaintenanceDoneIntervalKind("days");
    setMaintenanceDoneIntervalValue("");
    setMaintenanceDoneDisableReminder(false);
  }

  async function deleteLatestMaintenanceTaskEvent(taskId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await maintenanceApi.latestTaskEvent(taskId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function createDefaultMaintenanceTasks() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await maintenanceApi.createDefaults(selectedPrinterId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function submitMaintenanceFreeEvent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId || !maintenanceEventType || !maintenanceComponent.trim() || !maintenanceTitle.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const performedAt = new Date().toISOString();
      const response = await maintenanceApi.createEvent(selectedPrinterId, {
        event_type: maintenanceEventType,
        component: maintenanceComponent.trim(),
        title: maintenanceTitle.trim(),
        notes: maintenanceNotes,
        performed_at: performedAt,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const reminderValue = maintenanceFreeReminderEnabled && maintenanceFreeIntervalValue.trim()
        ? Number(maintenanceFreeIntervalValue)
        : null;
      if (maintenanceFreeReminderEnabled && maintenanceFreeIntervalKind === "print_hours" && !maintenancePrintHours?.available) {
        throw new Error("Horas de impressão indisponíveis. Ligue a impressora para usar lembrete por horas.");
      }
      if (reminderValue) {
        const taskResponse = await maintenanceApi.createTask(selectedPrinterId, {
          name: maintenanceTitle,
          component: maintenanceComponent.trim(),
          interval_days: maintenanceFreeIntervalKind === "days" ? reminderValue : 30,
          interval_kind: maintenanceFreeIntervalKind,
          interval_value: reminderValue,
          last_done_at: performedAt,
        });
        if (!taskResponse.ok) {
          throw new Error(await taskResponse.text());
        }
      }
      setMaintenanceEventType("");
      setMaintenanceComponent("");
      setMaintenanceTitle("");
      setMaintenanceNotes("");
      setMaintenanceFreeReminderEnabled(false);
      setMaintenanceFreeIntervalKind("days");
      setMaintenanceFreeIntervalValue("");
      setMaintenanceFreeModalOpen(false);
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function deleteMaintenanceEvent(eventId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await maintenanceApi.deleteEvent(eventId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const visibleMaintenanceTasks = maintenanceTasks.filter((task) => {
    if (maintenanceFilter === "all") {
      return true;
    }
    return task.due_status === maintenanceFilter;
  });
  const nextMaintenanceTask = maintenanceSummary?.next_due_task;
  const maintenancePrintHoursAvailable =
    maintenancePrintHours?.available && typeof maintenancePrintHours.total_print_hours === "number";
  const maintenanceHoursDisabledMessage = "Horas de impressão indisponíveis. Ligue a impressora para habilitar.";

  return {
    completeMaintenanceTask,
    createDefaultMaintenanceTasks,
    deleteLatestMaintenanceTaskEvent,
    deleteMaintenanceEvent,
    loadMaintenance,
    maintenanceComponent,
    maintenanceDoneDisableReminder,
    maintenanceDoneIntervalKind,
    maintenanceDoneIntervalValue,
    maintenanceDoneNotes,
    maintenanceDoneTask,
    maintenanceEventType,
    maintenanceEvents,
    maintenanceFilter,
    maintenanceFreeIntervalKind,
    maintenanceFreeIntervalValue,
    maintenanceFreeModalOpen,
    maintenanceFreeReminderEnabled,
    maintenanceHoursDisabledMessage,
    maintenanceNotes,
    maintenancePrintHours,
    maintenancePrintHoursAvailable,
    maintenanceSummary,
    maintenanceTasks,
    maintenanceTitle,
    nextMaintenanceTask,
    openMaintenanceDoneModal,
    openMaintenanceFreeModal,
    setMaintenanceComponent,
    setMaintenanceDoneDisableReminder,
    setMaintenanceDoneIntervalKind,
    setMaintenanceDoneIntervalValue,
    setMaintenanceDoneNotes,
    setMaintenanceDoneTask,
    setMaintenanceEventType,
    setMaintenanceEvents,
    setMaintenanceFilter,
    setMaintenanceFreeIntervalKind,
    setMaintenanceFreeIntervalValue,
    setMaintenanceFreeModalOpen,
    setMaintenanceFreeReminderEnabled,
    setMaintenanceNotes,
    setMaintenancePrintHours,
    setMaintenanceSummary,
    setMaintenanceTasks,
    setMaintenanceTitle,
    submitMaintenanceDone,
    submitMaintenanceFreeEvent,
    visibleMaintenanceTasks,
  };
}
