from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class ModerationAssessment:
    language: str
    labels: tuple[str, ...]
    confidence: float
    human_review_required: bool


LANGUAGE_MARKERS = {
    "pt": {"voce", "você", "nao", "não", "isso", "produto", "denuncia", "golpe"},
    "en": {"you", "this", "product", "report", "scam", "hate"},
    "es": {"usted", "esto", "producto", "denuncia", "estafa", "odio"},
}
LABEL_TERMS = {
    "spam": {"spam", "promo", "compre", "buy", "oferta", "offer", "gratis", "free"},
    "harassment": {"idiota", "imbecil", "hate", "stupid", "odio", "tonto"},
    "unsafe": {"arma", "weapon", "explosivo", "explosive", "bomba", "bomb"},
    "privacy": {"telefone", "phone", "endereco", "address", "cpf", "documento"},
}


def assess_text(text: str) -> ModerationAssessment:
    normalized = _normalize(text)
    terms = set(re.findall(r"[\wÀ-ÿ]+", normalized, re.UNICODE))
    language_scores = {
        language: len(terms.intersection(markers))
        for language, markers in LANGUAGE_MARKERS.items()
    }
    language = max(language_scores, key=language_scores.get)
    if language_scores[language] == 0:
        language = "und"
    labels = tuple(
        label for label, markers in LABEL_TERMS.items()
        if terms.intersection(markers)
    )
    if re.search(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", text, re.IGNORECASE):
        labels = tuple(sorted(set((*labels, "privacy"))))
    confidence = min(0.99, 0.35 + (0.2 * len(labels))) if labels else 0.2
    high_impact = bool(set(labels).intersection({"harassment", "unsafe", "privacy"}))
    return ModerationAssessment(language, labels, confidence, high_impact)


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.lower())
    return " ".join(
        "".join(character for character in decomposed if not unicodedata.combining(character))
        .replace("\n", " ")
        .split()
    )
