from app.firmware.models import BoardPreset, FirmwareConfigPreview


def generate_firmware_config_preview(preset: BoardPreset) -> FirmwareConfigPreview:
    validation = preset.build_config_validation
    if validation.status != "complete":
        details = ", ".join(validation.missing_fields + validation.invalid_fields)
        raise ValueError(f"preset build config is {validation.status}: {details}")
    config = preset.build_config
    if config is None:
        raise ValueError("preset build config is missing")
    lines = _config_lines(preset)
    content = "\n".join(lines) + "\n"
    return FirmwareConfigPreview(
        safe_mode="config_preview_only_no_write",
        preset_id=preset.id,
        config_file=config.config_file,
        build_output=config.build_output,
        build_config_schema_version=config.schema_version,
        content=content,
        lines=lines,
        artifact_saved=False,
        artifact_path=None,
        message="Preview gerado em memória. Nenhum arquivo foi salvo e nenhum comando foi executado.",
    )


def _config_lines(preset: BoardPreset) -> list[str]:
    config = preset.build_config
    if config is None:
        raise ValueError("preset build config is missing")
    values = [
        "# Printora firmware .config preview",
        f"# preset_id={preset.id}",
        f"# preset_name={preset.name}",
        f"# schema_version={config.schema_version}",
        "CONFIG_LOW_LEVEL_OPTIONS=y",
        *_architecture_lines(config.architecture),
        f'CONFIG_MCU="{config.mcu}"',
        f'CONFIG_PROCESSOR_MODEL="{config.processor_model}"',
        f'CONFIG_BOOTLOADER_OFFSET="{config.bootloader_offset}"',
        f'CONFIG_CLOCK_REFERENCE="{config.clock_reference}"',
        f'CONFIG_COMMUNICATION_INTERFACE="{config.communication_interface}"',
        f'CONFIG_CONNECTION_TYPE="{config.connection_type}"',
    ]
    if config.canbus_pins:
        values.append(f'CONFIG_CANBUS_PINS="{config.canbus_pins}"')
    if config.usb_pins:
        values.append(f'CONFIG_USB_PINS="{config.usb_pins}"')
    if config.serial_pins:
        values.append(f'CONFIG_SERIAL_PINS="{config.serial_pins}"')
    values.extend([
        f'CONFIG_PRINTORA_CONFIG_FILE="{config.config_file}"',
        f'CONFIG_PRINTORA_BUILD_OUTPUT="{config.build_output}"',
        "CONFIG_PRINTORA_FLASH_AUTOMATICO=n",
    ])
    return values


def _architecture_lines(architecture: str) -> list[str]:
    normalized = architecture.strip().lower()
    if normalized == "stm32":
        return ["CONFIG_MACH_STM32=y"]
    if normalized == "rp2040":
        return ["CONFIG_MACH_RP2040=y"]
    return [f'CONFIG_MACH_UNKNOWN="{architecture}"']
