from __future__ import annotations

from pathlib import Path

from .google_people import fetch_google_contacts
from .models import SyncStats
from .storage import ContactsRepository


def sync_google_contacts(
    *,
    credentials_path: Path,
    token_path: Path,
    db_path: Path,
    source_account: str = "default",
) -> SyncStats:
    repository = ContactsRepository(db_path)
    repository.initialize()
    sync_run_id = repository.begin_sync_run(source="google_people", source_account=source_account)

    try:
        contacts = fetch_google_contacts(
            credentials_path=credentials_path,
            token_path=token_path,
            source_account=source_account,
        )
        stats = repository.replace_contacts(
            source="google_people",
            source_account=source_account,
            contacts=contacts,
            sync_run_id=sync_run_id,
        )
    except Exception as exc:
        repository.finish_sync_run(
            sync_run_id=sync_run_id,
            status="failed",
            contacts_fetched=0,
            contacts_written=0,
            contacts_deactivated=0,
            error_message=str(exc),
        )
        raise

    repository.finish_sync_run(
        sync_run_id=sync_run_id,
        status="completed",
        contacts_fetched=stats.fetched_count,
        contacts_written=stats.written_count,
        contacts_deactivated=stats.deactivated_count,
    )
    return stats
