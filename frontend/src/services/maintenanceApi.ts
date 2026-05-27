import { apiResponse } from "./http";

export const maintenanceApi = {
  events: (printerId: number) => apiResponse(`/api/printers/${printerId}/maintenance/events`),
  tasks: (printerId: number) => apiResponse(`/api/printers/${printerId}/maintenance/tasks`),
  summary: (printerId: number) => apiResponse(`/api/printers/${printerId}/maintenance/summary`),
  createDefaults: (printerId: number) => apiResponse(`/api/printers/${printerId}/maintenance/tasks/defaults`, { method: "POST" }),
  printHours: (printerId: number) => apiResponse(`/api/printers/${printerId}/maintenance/print-hours`),
  completeTask: (taskId: number, body: unknown) =>
    apiResponse(`/api/maintenance/tasks/${taskId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  latestTaskEvent: (taskId: number) => apiResponse(`/api/maintenance/tasks/${taskId}/latest-event`, { method: "DELETE" }),
  updateTaskApplicability: (taskId: number, isApplicable: boolean) =>
    apiResponse(`/api/maintenance/tasks/${taskId}/applicability`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_applicable: isApplicable }),
    }),
  createEvent: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/maintenance/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  createTask: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/maintenance/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  deleteEvent: (eventId: number) => apiResponse(`/api/maintenance/events/${eventId}`, { method: "DELETE" }),
};
