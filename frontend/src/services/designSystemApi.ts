import { apiRequest } from "./http";
import type { DesignSystemCatalog } from "../types/designSystem";


export const designSystemApi = {
  catalog: () => apiRequest<DesignSystemCatalog>("/api/design-system/v1/capabilities"),
};
