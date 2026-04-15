from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .acn import AcnTimingClient, build_dataset, parse_acn_url
from .models import RaceFetchStats
from .storage import RaceResultsRepository


def fetch_acn_results(
    *,
    url: str,
    db_path: Path,
    raw_dir: Path,
) -> RaceFetchStats:
    descriptor = parse_acn_url(url)
    client = AcnTimingClient()
    payload = client.fetch(descriptor)

    raw_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_prefix = f"{descriptor.context_db}_{descriptor.report_key}_{timestamp}"

    raw_event_path = raw_dir / f"{safe_prefix}_event.json"
    raw_results_path = raw_dir / f"{safe_prefix}_results.json"

    raw_event_path.write_text(
        json.dumps(payload.event_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    raw_results_path.write_text(
        json.dumps(payload.results_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    dataset, results = build_dataset(payload)
    dataset.raw_event_path = str(raw_event_path)
    dataset.raw_results_path = str(raw_results_path)

    repository = RaceResultsRepository(db_path)
    repository.initialize()
    dataset_id = repository.save_dataset(dataset=dataset, results=results)

    return RaceFetchStats(dataset_id=dataset_id, results_count=len(results))
