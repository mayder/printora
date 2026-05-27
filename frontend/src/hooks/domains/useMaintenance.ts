import React from "react";
import { maintenanceApi } from "../../services/maintenanceApi";
import type { MaintenanceEventRecord, MaintenancePrintHoursStatus, MaintenanceSummary, MaintenanceTaskRecord } from "../../types";
import type { SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UseMaintenanceOptions = {
  selectedPrinterId: number | null;
  setError: SetError;
  setLoading: SetLoading;
};

type MaintenanceFilter = "all" | "due" | "soon" | "ok" | "not_applicable";
type MaintenanceSort = "area" | "title" | "criticality" | "due";

export function useMaintenance({ selectedPrinterId, setError, setLoading }: UseMaintenanceOptions) {
  const [maintenanceEvents, setMaintenanceEvents] = React.useState<MaintenanceEventRecord[]>([]);
  const [maintenanceTasks, setMaintenanceTasks] = React.useState<MaintenanceTaskRecord[]>([]);
  const [maintenanceSummary, setMaintenanceSummary] = React.useState<MaintenanceSummary | null>(null);
  const [maintenancePrintHours, setMaintenancePrintHours] = React.useState<MaintenancePrintHoursStatus | null>(null);
  const [maintenanceFilter, setMaintenanceFilter] = React.useState<MaintenanceFilter>("all");
  const [maintenanceTagFilter, setMaintenanceTagFilter] = React.useState("all");
  const [maintenanceSort, setMaintenanceSort] = React.useState<MaintenanceSort>("area");
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
    const hasRecommendedPrintHours =
      maintenancePrintHours?.available &&
      typeof maintenancePrintHours.total_print_hours === "number" &&
      task.recommended_interval_kind === "print_hours" &&
      typeof task.recommended_interval_value === "number";
    const intervalKind = hasRecommendedPrintHours ? "print_hours" : "days";
    const intervalValue = hasRecommendedPrintHours
      ? task.recommended_interval_value!
      : task.interval_kind === "days"
        ? task.interval_value || task.interval_days
        : task.interval_days;
    setMaintenanceDoneTask(task);
    setMaintenanceDoneNotes("");
    setMaintenanceDoneIntervalKind(intervalKind);
    setMaintenanceDoneIntervalValue(
      task.is_active
        ? formatMaintenanceRecommendedIntervalValue(intervalValue)
        : "",
    );
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

  async function updateMaintenanceTaskApplicability(taskId: number, isApplicable: boolean) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await maintenanceApi.updateTaskApplicability(taskId, isApplicable);
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

  const filteredMaintenanceTasks = maintenanceTasks.filter((task) => {
    if (maintenanceFilter === "all") {
      return task.is_applicable && taskMatchesMaintenanceTag(task, maintenanceTagFilter);
    }
    if (maintenanceFilter === "not_applicable") {
      return !task.is_applicable && taskMatchesMaintenanceTag(task, maintenanceTagFilter);
    }
    if (!task.is_applicable) {
      return false;
    }
    return task.due_status === maintenanceFilter && taskMatchesMaintenanceTag(task, maintenanceTagFilter);
  });
  const visibleMaintenanceTasks = [...filteredMaintenanceTasks].sort((first, second) => compareMaintenanceTasks(first, second, maintenanceSort));
  const maintenanceTagOptions = Array.from(
    new Set(maintenanceTasks.flatMap((task) => task.tags ?? [])),
  ).sort((first, second) => maintenanceTagSortValue(first) - maintenanceTagSortValue(second) || first.localeCompare(second));
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
    maintenanceSort,
    maintenanceSummary,
    maintenanceTagFilter,
    maintenanceTagOptions,
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
    setMaintenanceSort,
    setMaintenanceSummary,
    setMaintenanceTagFilter,
    setMaintenanceTasks,
    setMaintenanceTitle,
    submitMaintenanceDone,
    submitMaintenanceFreeEvent,
    updateMaintenanceTaskApplicability,
    visibleMaintenanceTasks,
  };
}

function formatMaintenanceRecommendedIntervalValue(value: number) {
  return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(1)));
}

function taskMatchesMaintenanceTag(task: MaintenanceTaskRecord, tagFilter: string) {
  return tagFilter === "all" || task.tags?.includes(tagFilter);
}

function maintenanceTagSortValue(tag: string) {
  const order = ["Filamento", "Toolhead", "Mesa", "Movimento", "Motores", "Refrigeração", "Elétrica", "Estrutura", "Calibração", "Acessórios", "Software"];
  const index = order.indexOf(tag);
  return index === -1 ? 999 : index;
}

function compareMaintenanceTasks(first: MaintenanceTaskRecord, second: MaintenanceTaskRecord, sort: MaintenanceSort) {
  if (sort === "title") {
    return compareByTitle(first, second);
  }
  if (sort === "criticality") {
    return maintenanceStatusSortValue(first) - maintenanceStatusSortValue(second) || compareByDue(first, second) || compareByTitle(first, second);
  }
  if (sort === "due") {
    return compareByDue(first, second) || maintenanceStatusSortValue(first) - maintenanceStatusSortValue(second) || compareByTitle(first, second);
  }
  return compareByArea(first, second) || maintenanceStatusSortValue(first) - maintenanceStatusSortValue(second) || compareByTitle(first, second);
}

function compareByArea(first: MaintenanceTaskRecord, second: MaintenanceTaskRecord) {
  const firstTag = first.primary_tag || first.tags?.[0] || "Geral";
  const secondTag = second.primary_tag || second.tags?.[0] || "Geral";
  return maintenanceTagSortValue(firstTag) - maintenanceTagSortValue(secondTag) || firstTag.localeCompare(secondTag);
}

function compareByDue(first: MaintenanceTaskRecord, second: MaintenanceTaskRecord) {
  return maintenanceDueSortValue(first) - maintenanceDueSortValue(second);
}

function compareByTitle(first: MaintenanceTaskRecord, second: MaintenanceTaskRecord) {
  return first.name.localeCompare(second.name);
}

function maintenanceStatusSortValue(task: MaintenanceTaskRecord) {
  const order: Record<MaintenanceTaskRecord["due_status"], number> = {
    due: 0,
    soon: 1,
    needs_review: 2,
    not_validated: 3,
    unknown: 4,
    ok: 5,
    not_applicable: 6,
  };
  return order[task.due_status] ?? 99;
}

function maintenanceDueSortValue(task: MaintenanceTaskRecord) {
  if (typeof task.days_until_due === "number") {
    return task.days_until_due;
  }
  if (typeof task.print_hours_until_due === "number") {
    return task.print_hours_until_due;
  }
  return Number.POSITIVE_INFINITY;
}
