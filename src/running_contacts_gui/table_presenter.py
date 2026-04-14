from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from running_contacts.matching.models import MatchReport, MatchResult


@dataclass(slots=True, frozen=True)
class TableView:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


class TablePresenter:
    """Centralize all table transformations and QTableWidget population."""

    def __init__(self, table: QTableWidget) -> None:
        self.table = table

    def show_placeholder(self, message: str) -> None:
        self._render(TableView(headers=("message",), rows=((message,),)))

    def show_contacts(self, contacts: list[dict[str, Any]]) -> None:
        rows = tuple(self._contact_row(contact) for contact in contacts)
        self._render(
            TableView(
                headers=("id", "display_name", "active", "methods", "aliases"),
                rows=rows,
            )
        )

    def show_datasets(self, datasets: list[dict[str, Any]]) -> None:
        rows = tuple(self._dataset_row(dataset) for dataset in datasets)
        self._render(
            TableView(
                headers=("id", "event_title", "event_date", "event_location", "report", "aliases", "rows"),
                rows=rows,
            )
        )

    def show_race_results(self, results: list[dict[str, Any]]) -> None:
        rows = tuple(self._race_result_row(result) for result in results)
        self._render(
            TableView(
                headers=("id", "position", "athlete_name", "finish_time", "team", "bib", "category"),
                rows=rows,
            )
        )

    def show_matches(self, report: MatchReport) -> None:
        rows = tuple(self._match_row(match) for match in report.accepted_matches)
        self._render(
            TableView(
                headers=(
                    "result_id",
                    "athlete_name",
                    "contact_name",
                    "match_method",
                    "score",
                    "position",
                    "finish_time",
                    "team",
                    "matched_alias",
                ),
                rows=rows,
            )
        )

    def _render(self, view: TableView) -> None:
        self.table.clear()
        self.table.setColumnCount(len(view.headers))
        self.table.setHorizontalHeaderLabels(list(view.headers))
        self.table.setRowCount(len(view.rows))

        for row_index, row in enumerate(view.rows):
            for column_index, value in enumerate(row):
                self.table.setItem(row_index, column_index, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()

    @staticmethod
    def _contact_row(contact: dict[str, Any]) -> tuple[str, ...]:
        methods = ", ".join(str(method["value"]) for method in contact.get("methods", []))
        aliases = ", ".join(str(alias) for alias in contact.get("aliases", []))
        return (
            str(contact.get("id", "")),
            str(contact.get("display_name", "")),
            "yes" if bool(contact.get("active")) else "no",
            methods,
            aliases,
        )

    @staticmethod
    def _dataset_row(dataset: dict[str, Any]) -> tuple[str, ...]:
        aliases = ", ".join(str(alias) for alias in dataset.get("aliases", []))
        report = f"{dataset.get('context_db', '')}/{dataset.get('report_key', '')}".strip("/")
        return (
            str(dataset.get("id", "")),
            str(dataset.get("event_title", "") or ""),
            str(dataset.get("event_date", "") or ""),
            str(dataset.get("event_location", "") or ""),
            report,
            aliases,
            str(dataset.get("total_results", "") or ""),
        )

    @staticmethod
    def _race_result_row(result: dict[str, Any]) -> tuple[str, ...]:
        return (
            str(result.get("id", "")),
            str(result.get("position_text", "") or ""),
            str(result.get("athlete_name", "") or ""),
            str(result.get("finish_time", "") or ""),
            str(result.get("team", "") or ""),
            str(result.get("bib", "") or ""),
            str(result.get("category", "") or ""),
        )

    @staticmethod
    def _match_row(match: MatchResult) -> tuple[str, ...]:
        return (
            str(match.result_id),
            match.athlete_name,
            match.contact_name or "",
            match.match_method,
            f"{match.score:.1f}",
            match.position_text or "",
            match.finish_time or "",
            match.team or "",
            match.matched_alias or "",
        )
