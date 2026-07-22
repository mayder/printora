from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_INCLUDE_PATTERNS = ["**/*.cfg", "**/*.conf", "**/*.md", "**/*.json"]


DEFAULT_EXCLUDE_PATTERNS = [
    "**/.git/**",
    "**/__pycache__/**",
    "**/*.log",
    "**/*.tmp",
    "**/*.bak",
    "**/*backup*",
    "**/*secret*",
    "**/*token*",
    "**/*password*",
    "moonraker.asvc",
]


class BackupPolicyCreate(BaseModel):
    name: str = Field(default="Config backup", min_length=1, max_length=80)
    source_path: str = Field(default="/home/pi/printer_data/config", min_length=1, max_length=300)
    destination_path: str = Field(
        default="/home/pi/printer_data/backups/printora",
        min_length=1,
        max_length=300,
    )
    include_patterns: list[str] = Field(default_factory=lambda: DEFAULT_INCLUDE_PATTERNS.copy())
    exclude_patterns: list[str] = Field(default_factory=lambda: DEFAULT_EXCLUDE_PATTERNS.copy())
    dry_run_only: bool = True


class BackupPolicyRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    name: str
    source_path: str
    destination_path: str
    include_patterns: list[str]
    exclude_patterns: list[str]
    dry_run_only: bool
    is_active: bool
    created_at: str
    updated_at: str


class BackupRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    policy_id: int
    created_at: str
    status: str
    dry_run: bool
    source_path: str
    destination_path: str
    include_patterns: list[str]
    exclude_patterns: list[str]
    total_files: int
    total_bytes: int
    message: str


class BackupArchiveCompareRequest(BaseModel):
    base_archive_path: str = Field(min_length=1, max_length=400)
    target_archive_path: str = Field(min_length=1, max_length=400)


class BackupArchiveCompareResponse(BaseModel):
    safe_mode: str
    base_archive_path: str
    target_archive_path: str
    added: list[str]
    removed: list[str]
    changed: list[str]
    unchanged_count: int
    summary: str


class BackupRestorePlanRequest(BaseModel):
    archive_path: str = Field(min_length=1, max_length=400)
    restore_root: str = Field(min_length=1, max_length=400)
    files: list[str] = Field(default_factory=list)


class BackupRestorePlanResponse(BaseModel):
    safe_mode: str
    archive_path: str
    restore_root: str
    selected_files: list[str]
    missing_files: list[str]
    planned_commands: list[str]
    blocked: bool
    message: str


class BackupRestoreExecuteRequest(BackupRestorePlanRequest):
    confirmation: str = Field(default="", max_length=100)


class BackupRestoreGateResponse(BaseModel):
    safe_mode: str
    accepted_confirmation: bool
    blocked: bool
    plan: BackupRestorePlanResponse
    rollback_plan: list[str]
    message: str

