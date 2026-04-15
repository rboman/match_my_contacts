from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from .models import RaceDataset, RaceResultRow

PROVIDER_NAME = "acn_timing"
EVENTS_API_BASE = "https://prod.chronorace.be/api/"
RESULTS_API_BASE = "https://results.chronorace.be/api/"


class AcnError(RuntimeError):
    """Raised when an ACN Timing URL or API response cannot be handled."""


@dataclass(slots=True)
class AcnRaceDescriptor:
    source_url: str
    event_id: str
    context_db: str
    report_path: str
    report_key: str


@dataclass(slots=True)
class AcnFetchedPayload:
    descriptor: AcnRaceDescriptor
    event_payload: dict[str, Any]
    results_payload: dict[str, Any]


class AcnTimingClient:
    def __init__(
        self,
        *,
        events_api_base: str = EVENTS_API_BASE,
        results_api_base: str = RESULTS_API_BASE,
        timeout: float = 30.0,
    ) -> None:
        self.events_api_base = events_api_base.rstrip("/") + "/"
        self.results_api_base = results_api_base.rstrip("/") + "/"
        self.timeout = timeout

    def fetch(self, descriptor: AcnRaceDescriptor) -> AcnFetchedPayload:
        event_payload = self._get_json(f"{self.events_api_base}Event/view/{descriptor.event_id}")
        results_payload = self._get_json(
            f"{self.results_api_base}results/table/search/{descriptor.context_db}/{descriptor.report_key}?srch="
        )
        return AcnFetchedPayload(
            descriptor=descriptor,
            event_payload=event_payload,
            results_payload=results_payload,
        )

    def _get_json(self, url: str) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "match-my-contacts/0.1",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise AcnError(f"ACN request failed with HTTP {response.status}: {url}")
                payload = response.read()
        except Exception as exc:
            if isinstance(exc, AcnError):
                raise
            raise AcnError(f"Failed to fetch ACN endpoint: {url}") from exc

        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise AcnError(f"ACN endpoint did not return valid JSON: {url}") from exc


def parse_acn_url(url: str) -> AcnRaceDescriptor:
    parsed = urlparse(url)
    fragment = unquote(parsed.fragment or "")
    fragment_parts = [part for part in fragment.split("/") if part]

    try:
        event_id = fragment_parts[fragment_parts.index("events") + 1]
        context_db = fragment_parts[fragment_parts.index("ctx") + 1]
        report_path = fragment_parts[fragment_parts.index("generic") + 1]
        report_key = fragment_parts[fragment_parts.index("home") + 1]
    except (ValueError, IndexError) as exc:
        raise AcnError(
            "Unsupported ACN Timing URL. Expected a fragment like "
            "#/events/<event_id>/ctx/<db>/generic/<path>/home/<report_key>."
        ) from exc

    return AcnRaceDescriptor(
        source_url=url,
        event_id=event_id,
        context_db=context_db,
        report_path=report_path,
        report_key=report_key,
    )


def build_dataset(payload: AcnFetchedPayload) -> tuple[RaceDataset, list[RaceResultRow]]:
    event_payload = payload.event_payload
    results_payload = payload.results_payload
    descriptor = payload.descriptor

    dataset = RaceDataset(
        provider=PROVIDER_NAME,
        source_url=descriptor.source_url,
        external_event_id=descriptor.event_id,
        context_db=descriptor.context_db,
        report_key=descriptor.report_key,
        report_path=descriptor.report_path,
        event_title=event_payload.get("Title"),
        event_date=event_payload.get("Date"),
        event_location=event_payload.get("Location"),
        event_country=event_payload.get("Country"),
        total_results=int(results_payload.get("Count") or 0),
        metadata={
            "event": {
                "event_id": event_payload.get("EventId"),
                "title": event_payload.get("Title"),
                "date": event_payload.get("Date"),
                "location": event_payload.get("Location"),
                "country": event_payload.get("Country"),
                "db": event_payload.get("Parameters", {}).get("db"),
            },
            "settings": results_payload.get("Settings", {}),
            "columns": results_payload.get("TableDefinition", {}).get("Columns", []),
        },
    )

    rows: list[RaceResultRow] = []
    for group_rank, group in enumerate(results_payload.get("Groups", []), start=1):
        group_name = group.get("Name") or group.get("Id") or None
        for row in group.get("SlaveRows", []):
            parsed_row = _normalize_row(
                row=row,
                columns=results_payload.get("TableDefinition", {}).get("Columns", []),
                group_name=group_name,
                group_rank=group_rank,
            )
            if parsed_row:
                rows.append(parsed_row)

    return dataset, rows


def _normalize_row(
    *,
    row: list[Any],
    columns: list[dict[str, Any]],
    group_name: str | None,
    group_rank: int,
) -> RaceResultRow | None:
    athlete_name = _row_value(columns, row, token="#NAME")
    if not athlete_name:
        return None

    row_action = _row_value(columns, row, exact_name="sH_RowAction")
    detail_token = None
    if isinstance(row_action, str) and row_action.startswith("detail:"):
        detail_token = row_action.split(":", 1)[1]

    return RaceResultRow(
        group_name=group_name,
        group_rank=group_rank,
        position_text=_row_value(columns, row, exact_name="sR_Pos", display_name="Pos"),
        bib=_row_value(columns, row, token="#NR"),
        athlete_name=athlete_name,
        team=_row_value(columns, row, token="#TEAM"),
        country=_row_value(columns, row, token="#NOC"),
        gender=_row_value(columns, row, token="#GENDER"),
        location=_row_value(columns, row, token="#LOCATION"),
        finish_time=_row_value(columns, row, token="#TIME"),
        pace_text=_row_value(columns, row, token="#AVG"),
        category_rank=_row_value(columns, row, display_name="Rang", group_display_name="Categ"),
        category=_row_value(columns, row, token="#CAT"),
        detail_token=detail_token,
        row_class=_row_value(columns, row, exact_name="sH_RowClass"),
        raw_row=list(row),
    )


def _row_value(
    columns: list[dict[str, Any]],
    row: list[Any],
    *,
    token: str | None = None,
    exact_name: str | None = None,
    display_name: str | None = None,
    group_display_name: str | None = None,
) -> str | None:
    for column in columns:
        column_name = column.get("Name")
        if exact_name and column_name != exact_name:
            continue
        if token and token not in str(column_name) and token not in str(column.get("DisplayName")):
            continue
        if display_name and column.get("DisplayName") != display_name:
            continue
        if group_display_name and column.get("GroupDisplayName") != group_display_name:
            continue

        index = column.get("FieldIdx")
        if not isinstance(index, int) or index >= len(row):
            return None
        value = row[index]
        if value is None:
            return None
        text = str(value).strip()
        return text or None
    return None
