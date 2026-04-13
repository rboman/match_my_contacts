from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import RaceDataset, RaceResultRow


class RaceResultsRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS race_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    external_event_id TEXT NOT NULL,
                    context_db TEXT NOT NULL,
                    report_key TEXT NOT NULL,
                    report_path TEXT NOT NULL,
                    event_title TEXT,
                    event_date TEXT,
                    event_location TEXT,
                    event_country TEXT,
                    total_results INTEGER NOT NULL DEFAULT 0,
                    raw_event_path TEXT,
                    raw_results_path TEXT,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(provider, context_db, report_key)
                );

                CREATE TABLE IF NOT EXISTS race_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    group_name TEXT,
                    group_rank INTEGER NOT NULL,
                    position_text TEXT,
                    bib TEXT,
                    athlete_name TEXT NOT NULL,
                    team TEXT,
                    country TEXT,
                    gender TEXT,
                    location TEXT,
                    finish_time TEXT,
                    pace_text TEXT,
                    category_rank TEXT,
                    category TEXT,
                    detail_token TEXT,
                    row_class TEXT,
                    raw_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(dataset_id) REFERENCES race_datasets(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_race_results_dataset_id ON race_results(dataset_id);
                CREATE INDEX IF NOT EXISTS idx_race_results_athlete_name ON race_results(athlete_name);
                """
            )

    def save_dataset(self, *, dataset: RaceDataset, results: list[RaceResultRow]) -> int:
        metadata_json = json.dumps(dataset.metadata, ensure_ascii=False, sort_keys=True)

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO race_datasets (
                    provider,
                    source_url,
                    external_event_id,
                    context_db,
                    report_key,
                    report_path,
                    event_title,
                    event_date,
                    event_location,
                    event_country,
                    total_results,
                    raw_event_path,
                    raw_results_path,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, context_db, report_key) DO UPDATE SET
                    source_url = excluded.source_url,
                    external_event_id = excluded.external_event_id,
                    report_path = excluded.report_path,
                    event_title = excluded.event_title,
                    event_date = excluded.event_date,
                    event_location = excluded.event_location,
                    event_country = excluded.event_country,
                    total_results = excluded.total_results,
                    raw_event_path = excluded.raw_event_path,
                    raw_results_path = excluded.raw_results_path,
                    metadata_json = excluded.metadata_json,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (
                    dataset.provider,
                    dataset.source_url,
                    dataset.external_event_id,
                    dataset.context_db,
                    dataset.report_key,
                    dataset.report_path,
                    dataset.event_title,
                    dataset.event_date,
                    dataset.event_location,
                    dataset.event_country,
                    dataset.total_results,
                    dataset.raw_event_path,
                    dataset.raw_results_path,
                    metadata_json,
                ),
            )
            dataset_id = int(cursor.fetchone()["id"])
            conn.execute("DELETE FROM race_results WHERE dataset_id = ?", (dataset_id,))
            conn.executemany(
                """
                INSERT INTO race_results (
                    dataset_id,
                    group_name,
                    group_rank,
                    position_text,
                    bib,
                    athlete_name,
                    team,
                    country,
                    gender,
                    location,
                    finish_time,
                    pace_text,
                    category_rank,
                    category,
                    detail_token,
                    row_class,
                    raw_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        dataset_id,
                        result.group_name,
                        result.group_rank,
                        result.position_text,
                        result.bib,
                        result.athlete_name,
                        result.team,
                        result.country,
                        result.gender,
                        result.location,
                        result.finish_time,
                        result.pace_text,
                        result.category_rank,
                        result.category,
                        result.detail_token,
                        result.row_class,
                        json.dumps(result.raw_row, ensure_ascii=False),
                    )
                    for result in results
                ],
            )
            return dataset_id

    def list_datasets(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id,
                       provider,
                       event_title,
                       event_date,
                       event_location,
                       context_db,
                       report_key,
                       total_results,
                       updated_at
                FROM race_datasets
                ORDER BY updated_at DESC, id DESC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def list_results(
        self,
        *,
        dataset_id: int,
        query: str | None = None,
        limit: int | None = 20,
    ) -> list[dict[str, Any]]:
        sql = """
            SELECT id,
                   dataset_id,
                   position_text,
                   bib,
                   athlete_name,
                   team,
                   country,
                   gender,
                   location,
                   finish_time,
                   pace_text,
                   category_rank,
                   category,
                   detail_token
            FROM race_results
            WHERE dataset_id = ?
        """
        params: list[Any] = [dataset_id]

        if query:
            sql += """
                AND (
                    athlete_name LIKE ?
                    OR COALESCE(team, '') LIKE ?
                    OR COALESCE(bib, '') LIKE ?
                )
            """
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query])

        sql += " ORDER BY id"

        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def export_dataset(self, *, dataset_id: int) -> dict[str, Any]:
        with self._connect() as conn:
            dataset = conn.execute(
                """
                SELECT *
                FROM race_datasets
                WHERE id = ?
                """,
                (dataset_id,),
            ).fetchone()
            if dataset is None:
                raise KeyError(f"Dataset {dataset_id} not found")

            results = conn.execute(
                """
                SELECT position_text,
                       bib,
                       athlete_name,
                       team,
                       country,
                       gender,
                       location,
                       finish_time,
                       pace_text,
                       category_rank,
                       category,
                       detail_token
                FROM race_results
                WHERE dataset_id = ?
                ORDER BY id
                """,
                (dataset_id,),
            ).fetchall()

        payload = dict(dataset)
        payload["metadata"] = json.loads(payload.pop("metadata_json"))
        payload["results"] = [dict(row) for row in results]
        return payload

    def write_export_json(self, *, dataset_id: int, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.export_dataset(dataset_id=dataset_id)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
