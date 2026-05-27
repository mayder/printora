from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator




ConnectionType = Literal["usb", "can", "usb_can_bridge"]
FlashMethod = Literal["katapult_can", "katapult_usb_can", "dfu_usb", "manual"]
BuildConfigStatus = Literal["complete", "missing_data", "invalid"]


class FirmwareBuildConfig(BaseModel):
    schema_version: int = Field(default=1, ge=1)
    architecture: str = Field(min_length=1)
    mcu: str = Field(min_length=1)
    processor_model: str = Field(min_length=1)
    bootloader_offset: str = Field(min_length=1)
    clock_reference: str = Field(min_length=1)
    communication_interface: str = Field(min_length=1)
    connection_type: ConnectionType
    canbus_pins: str | None = None
    usb_pins: str | None = None
    serial_pins: str | None = None
    config_file: str = Field(min_length=1)
    build_output: str = Field(min_length=1)

    @field_validator("config_file")
    @classmethod
    def validate_config_file(cls, value: str) -> str:
        if not value.endswith(".config"):
            raise ValueError("config_file must end with .config")
        return value

    @field_validator("build_output")
    @classmethod
    def validate_build_output(cls, value: str) -> str:
        if not value.startswith("out/"):
            raise ValueError("build_output must be inside out/")
        if not value.endswith((".bin", ".uf2")):
            raise ValueError("build_output must end with .bin or .uf2")
        return value


class FirmwareBuildConfigValidation(BaseModel):
    status: BuildConfigStatus
    missing_fields: list[str] = Field(default_factory=list)
    invalid_fields: list[str] = Field(default_factory=list)


class FirmwareConfigPreview(BaseModel):
    safe_mode: str
    preset_id: str
    config_file: str
    build_output: str
    build_config_schema_version: int
    content: str
    lines: list[str]
    artifact_saved: bool
    artifact_path: str | None = None
    message: str


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
    config_file: str
    build_output: str
    default_flash_method: FlashMethod
    build_config: FirmwareBuildConfig | None = None
    notes: str

    @model_validator(mode="after")
    def fill_default_build_config(self) -> "BoardPreset":
        if self.build_config is None:
            self.build_config = FirmwareBuildConfig(
                architecture=self.architecture,
                mcu=self.mcu,
                processor_model=self.mcu.upper(),
                bootloader_offset=self.bootloader_offset,
                clock_reference=_default_clock_reference(self.mcu),
                communication_interface=self.communication,
                connection_type=self.connection_type,
                canbus_pins=self.canbus_pins,
                usb_pins="PA11/PA12" if self.connection_type in {"usb", "usb_can_bridge"} and self.architecture == "stm32" else None,
                serial_pins=None,
                config_file=self.config_file,
                build_output=self.build_output,
            )
        return self

    @computed_field
    @property
    def build_config_validation(self) -> FirmwareBuildConfigValidation:
        return validate_preset_build_config(self)

    @computed_field
    @property
    def build_config_status(self) -> BuildConfigStatus:
        return self.build_config_validation.status


def validate_preset_build_config(preset: BoardPreset) -> FirmwareBuildConfigValidation:
    config = preset.build_config
    if config is None:
        return FirmwareBuildConfigValidation(status="missing_data", missing_fields=["build_config"])

    required_values = {
        "architecture": config.architecture,
        "mcu": config.mcu,
        "processor_model": config.processor_model,
        "bootloader_offset": config.bootloader_offset,
        "clock_reference": config.clock_reference,
        "communication_interface": config.communication_interface,
        "connection_type": config.connection_type,
        "config_file": config.config_file,
        "build_output": config.build_output,
    }
    missing_fields = [field for field, value in required_values.items() if not str(value).strip()]
    expected_values = {
        "architecture": preset.architecture,
        "mcu": preset.mcu,
        "bootloader_offset": preset.bootloader_offset,
        "connection_type": preset.connection_type,
        "config_file": preset.config_file,
        "build_output": preset.build_output,
    }
    invalid_fields = [
        field
        for field, expected in expected_values.items()
        if str(getattr(config, field)).strip() != str(expected).strip()
    ]
    if invalid_fields:
        status: BuildConfigStatus = "invalid"
    elif missing_fields:
        status = "missing_data"
    else:
        status = "complete"
    return FirmwareBuildConfigValidation(
        status=status,
        missing_fields=missing_fields,
        invalid_fields=invalid_fields,
    )


def _default_clock_reference(mcu: str) -> str:
    lowered = mcu.lower()
    if lowered.startswith("stm32h7"):
        return "25 MHz crystal"
    if lowered.startswith("stm32f4"):
        return "12 MHz crystal"
    if lowered.startswith("stm32g0"):
        return "8 MHz crystal"
    if lowered.startswith("stm32f0"):
        return "8 MHz crystal"
    if lowered == "rp2040":
        return "12 MHz crystal"
    return "unknown"


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
    preset_id: str | None = None
    preset_build_config_status: BuildConfigStatus | None = None
    generated_config_path: str | None = None
    work_dir: str | None = None
    expected_build_output: str | None = None
    log_path: str | None = None
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
