def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value.strip()).strip("-") or "board"



def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _excerpt(output: str, max_lines: int = 20) -> str:
    lines = [line for line in output.splitlines() if line.strip()]
    return "\n".join(lines[-max_lines:]) if lines else "sem saída relevante"
