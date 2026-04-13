from __future__ import annotations

import re


_PHONE_CHARS_RE = re.compile(r"[^\d+]+")


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_phone(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("+"):
        return "+" + _PHONE_CHARS_RE.sub("", stripped[1:])
    return _PHONE_CHARS_RE.sub("", stripped)
