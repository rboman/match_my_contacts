from __future__ import annotations

import re
import unicodedata


_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_person_name(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = _NON_ALNUM_RE.sub(" ", text)
    return " ".join(text.split())


def normalize_person_name_tokens(value: str | None) -> str:
    normalized = normalize_person_name(value)
    if not normalized:
        return ""
    return " ".join(sorted(normalized.split()))
