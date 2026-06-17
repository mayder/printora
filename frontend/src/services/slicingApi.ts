import { apiRequest } from "./http";

export type SlicingEngineInfo = {
  engine: "orcaslicer" | "prusaslicer";
  status: "ready" | "blocked";
  configured_path: string | null;
  detected_path: string | null;
  version_text: string | null;
  warnings: string[];
  installation_hint: string;
  safe_mode: string;
};

export const slicingApi = {
  engine: () => apiRequest<SlicingEngineInfo>("/api/slicing/engine"),
};
