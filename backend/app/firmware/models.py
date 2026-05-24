from typing import Literal

from pydantic import BaseModel, ConfigDict, Field




ConnectionType = Literal["usb", "can", "usb_can_bridge"]
FlashMethod = Literal["katapult_can", "katapult_usb_can", "dfu_usb", "manual"]


class BoardPreset(BaseModel):
    id: str
    vendor: str
    name: str
    mcu: str
    architecture: str
    connection_type: ConnectionType
    communication: str
    bootloader_offset: str
    canbus_pins: str | None
    build_output: str
    default_flash_method: FlashMethod
    notes: str


class FirmwareBoardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    preset_id: str = Field(min_length=1, max_length=120)
    can_uuid: str | None = Field(default=None, max_length=64)
    can_interface: str = Field(default="can0", min_length=1, max_length=40)
    config_file: str | None = Field(default=None, max_length=160)
    notes: str = Field(default="", max_length=1000)


class FirmwareBoardRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    name: str
    preset_id: str
    can_uuid: str | None
    can_interface: str
    connection_type: ConnectionType
    mcu: str
    flash_method: FlashMethod
    config_file: str
    notes: str
    is_active: bool
    created_at: str
    updated_at: str


class FirmwareBuildDryRunCreate(BaseModel):
    klipper_path: str = Field(default="~/klipper", min_length=1, max_length=200)
    output_root: str = Field(default="~/printer_data/firmware_builds", min_length=1, max_length=240)
    notes: str = Field(default="", max_length=1000)


class FirmwareBuildExecuteCreate(FirmwareBuildDryRunCreate):
    confirmation: str = Field(default="", max_length=80)


class FirmwareBuildRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    board_id: int
    created_at: str
    status: str
    klipper_path: str
    output_dir: str
    config_backup_path: str
    binary_output_path: str
    commands: list[str]
    checklist: list[str]
    message: str


class FirmwareBuildPreflightCheck(BaseModel):
    key: str
    label: str
    status: Literal["ok", "warning", "blocked"]
    detail: str


class FirmwareBuildPreflight(BaseModel):
    safe_mode: str
    printer_id: int
    board_id: int
    board_name: str
    klipper_path: str
    output_root: str
    config_file: str
    expected_build_output: str
    checks: list[FirmwareBuildPreflightCheck]
    commands_preview: list[str]
    blocked: bool
    can_execute_build: bool
    message: str


class FirmwareFlashDryRunCreate(BaseModel):
    build_run_id: int | None = None
    binary_path: str | None = Field(default=None, max_length=260)
    notes: str = Field(default="", max_length=1000)


class FirmwareFlashExecuteCreate(FirmwareFlashDryRunCreate):
    confirmation: str = Field(default="", max_length=100)


class FirmwareFlashRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    board_id: int
    build_run_id: int | None
    created_at: str
    status: str
    flash_method: FlashMethod
    can_uuid: str | None
    can_interface: str
    binary_path: str
    commands: list[str]
    checklist: list[str]
    message: str


class FirmwareFlashPreflightCheck(BaseModel):
    key: str
    label: str
    status: Literal["ok", "warning", "blocked"]
    detail: str


class FirmwareFlashPreflight(BaseModel):
    safe_mode: str
    printer_id: int
    board_id: int
    board_name: str
    flash_method: FlashMethod
    can_uuid: str | None
    can_interface: str
    binary_path: str
    connected: bool
    printing: bool
    print_state: str
    klipper_state: str | None
    klippy_state: str | None
    checks: list[FirmwareFlashPreflightCheck]
    commands_preview: list[str]
    rollback_plan: list[str]
    blocked: bool
    can_execute_flash: bool
    message: str


class FirmwareRecoveryPlan(BaseModel):
    safe_mode: str
    printer_id: int
    board_id: int
    board_name: str
    flash_method: FlashMethod
    can_uuid: str | None
    can_interface: str
    prerequisites: list[str]
    recovery_steps: list[str]
    validation_steps: list[str]
    rollback_notes: list[str]
    blocked: bool
