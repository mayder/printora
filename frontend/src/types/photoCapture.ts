export type PhotoCaptureStatus = "draft" | "review" | "ready" | "cancelled" | "expired";
export type PhotoHeightBand = "low" | "middle" | "high";
export type PhotoScaleMethod = "none" | "known_measurement" | "marker";

export interface PhotoCapturePhoto {
  id: number;
  capture_index: number;
  height_band: PhotoHeightBand;
  file_name: string;
  sha256: string;
  size_bytes: number;
  width: number;
  height: number;
  quality_status: "accepted" | "needs_review";
  issues: string[];
}

export interface PhotoCaptureSession {
  id: number;
  project_id: number;
  status: PhotoCaptureStatus;
  target_photo_count: number;
  scale_method: PhotoScaleMethod;
  scale_value_mm: number | null;
  scale_uncertainty_mm: number | null;
  scale_confirmed: boolean;
  consent_confirmed: boolean;
  expires_at: string;
  created_at: string;
  updated_at: string;
  photos: PhotoCapturePhoto[];
  accepted_photo_count: number;
  covered_photo_count: number;
  accepted_by_height_band: Record<PhotoHeightBand, number>;
  required_by_height_band: Record<PhotoHeightBand, number>;
  missing_height_bands: PhotoHeightBand[];
  next_actions: string[];
  can_complete: boolean;
}
