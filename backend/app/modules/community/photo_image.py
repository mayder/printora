from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError


MAX_PIXELS = 40_000_000


def sanitize_photo(file_name: str, body: bytes) -> tuple[bytes, str, int, int]:
    lowered = file_name.lower()
    expected = "JPEG" if lowered.endswith((".jpg", ".jpeg")) else "PNG" if lowered.endswith(".png") else None
    if expected is None:
        raise ValueError("use fotos JPEG ou PNG; HEIC ainda não está disponível neste dispositivo")
    try:
        with Image.open(BytesIO(body)) as candidate:
            if candidate.format != expected:
                raise ValueError(f"o conteúdo não é uma foto {expected} válida")
            if getattr(candidate, "is_animated", False):
                raise ValueError("use uma foto estática")
            if candidate.width <= 0 or candidate.height <= 0 or candidate.width * candidate.height > MAX_PIXELS:
                raise ValueError("a resolução da foto está fora do limite seguro")
            candidate.verify()
        with Image.open(BytesIO(body)) as source:
            width, height = source.size
            if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
                raise ValueError("a resolução da foto está fora do limite seguro")
            normalized = ImageOps.exif_transpose(source)
            width, height = normalized.size
            if expected == "JPEG":
                normalized = normalized.convert("RGB")
            elif normalized.mode not in {"RGB", "RGBA"}:
                normalized = normalized.convert("RGBA" if "transparency" in normalized.info else "RGB")
            output = BytesIO()
            if expected == "JPEG":
                normalized.save(output, format="JPEG", quality=92, optimize=True)
            else:
                normalized.save(output, format="PNG", optimize=True)
            return output.getvalue(), "image/jpeg" if expected == "JPEG" else "image/png", width, height
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValueError(f"o conteúdo não é uma foto {expected} válida") from exc


def inspect_photo_quality(body: bytes, width: int, height: int) -> tuple[list[str], dict[str, float | bool]]:
    with Image.open(BytesIO(body)) as source:
        sample = source.convert("L")
        sample.thumbnail((320, 320))
        brightness = float(ImageStat.Stat(sample).mean[0])
        edges = sample.filter(ImageFilter.FIND_EDGES)
        if edges.width > 4 and edges.height > 4:
            edges = edges.crop((2, 2, edges.width - 2, edges.height - 2))
        focus_score = float(ImageStat.Stat(edges).var[0])
    issues: list[str] = []
    if min(width, height) < 1080:
        issues.append("A foto tem pouca resolução; aproxime-se e fotografe novamente.")
    if brightness < 35:
        issues.append("A foto está escura; aumente a iluminação sem mover o objeto.")
    elif brightness > 225:
        issues.append("A foto está clara demais; reduza a luz direta e tente novamente.")
    if focus_score < 45:
        issues.append("A foto parece desfocada; firme o celular e toque no objeto para focar.")
    return issues, {
        "brightness": round(brightness, 2),
        "focus_score": round(focus_score, 2),
        "metadata_removed": True,
    }
