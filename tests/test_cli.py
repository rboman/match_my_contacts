from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from running_contacts.cli import app
from running_contacts.contacts.models import SyncStats
from running_contacts.contacts.storage import ContactsRepository


runner = CliRunner()


def test_contacts_sync_command(monkeypatch: object, tmp_path: Path) -> None:
    credentials_path = tmp_path / "credentials.json"
    credentials_path.write_text("{}", encoding="utf-8")
    db_path = tmp_path / "contacts.sqlite3"
    token_path = tmp_path / "token.json"

    def fake_sync_google_contacts(**_: object) -> SyncStats:
        return SyncStats(fetched_count=3, written_count=3, deactivated_count=0, sync_run_id=1)

    monkeypatch.setattr("running_contacts.cli.sync_google_contacts", fake_sync_google_contacts)

    result = runner.invoke(
        app,
        [
            "contacts",
            "sync",
            "--credentials",
            str(credentials_path),
            "--db-path",
            str(db_path),
            "--token-path",
            str(token_path),
        ],
    )

    assert result.exit_code == 0
    assert "3 fetched, 3 written, 0 deactivated" in result.stdout


def test_contacts_list_command_reads_local_database(tmp_path: Path) -> None:
    db_path = tmp_path / "contacts.sqlite3"
    repository = ContactsRepository(db_path)
    repository.initialize()
    sync_run_id = repository.begin_sync_run(source="google_people", source_account="default")
    repository.replace_contacts(
        source="google_people",
        source_account="default",
        contacts=[],
        sync_run_id=sync_run_id,
    )

    result = runner.invoke(app, ["contacts", "list", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "No contacts found." in result.stdout
