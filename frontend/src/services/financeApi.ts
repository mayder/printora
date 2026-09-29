import { apiRequest } from "./http";
import type { FinanceOverview, FinanceReadiness } from "../types/finance";

export const financeApi = {
  overview: () => apiRequest<FinanceOverview>("/api/admin/finance/overview"),
  readiness: () => apiRequest<FinanceReadiness>("/api/admin/finance/readiness"),
};
