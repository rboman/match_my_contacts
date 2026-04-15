from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ContactMethod:
    kind: str
    value: str
    label: str | None = None
    normalized_value: str | None = None
    is_primary: bool = False


@dataclass(slots=True)
class ContactRecord:
    source_contact_id: str
    display_name: str
    source: str = "google_people"
    source_account: str = "default"
    given_name: str | None = None
    family_name: str | None = None
    nickname: str | None = None
    organization: str | None = None
    notes: str | None = None
    methods: list[ContactMethod] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SyncStats:
    fetched_count: int
    written_count: int
    deactivated_count: int
    sync_run_id: int
