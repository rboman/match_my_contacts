from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RaceResultRow:
    group_name: str | None
    group_rank: int
    position_text: str | None
    bib: str | None
    athlete_name: str
    team: str | None = None
    country: str | None = None
    gender: str | None = None
    location: str | None = None
    finish_time: str | None = None
    pace_text: str | None = None
    category_rank: str | None = None
    category: str | None = None
    detail_token: str | None = None
    row_class: str | None = None
    raw_row: list[Any] = field(default_factory=list)


@dataclass(slots=True)
class RaceDataset:
    provider: str
    source_url: str
    external_event_id: str
    context_db: str
    report_key: str
    report_path: str
    event_title: str | None
    event_date: str | None
    event_location: str | None
    event_country: str | None
    total_results: int
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_event_path: str | None = None
    raw_results_path: str | None = None
    dataset_id: int | None = None


@dataclass(slots=True)
class RaceFetchStats:
    dataset_id: int
    results_count: int
