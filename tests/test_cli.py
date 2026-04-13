from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from running_contacts.cli import app
from running_contacts.contacts.models import SyncStats
from running_contacts.contacts.storage import ContactsRepository
from running_contacts.race_results.models import RaceFetchStats
from running_contacts.race_results.storage import RaceResultsRepository


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


def test_contacts_sync_uses_default_credentials_file(monkeypatch: object, tmp_path: Path) -> None:
    credentials_path = tmp_path / "credentials.json"
    credentials_path.write_text("{}", encoding="utf-8")
    db_path = tmp_path / "contacts.sqlite3"
    token_path = tmp_path / "token.json"
    captured: dict[str, Path] = {}

    def fake_sync_google_contacts(**kwargs: object) -> SyncStats:
        captured["credentials_path"] = kwargs["credentials_path"]  # type: ignore[index]
        return SyncStats(fetched_count=1, written_count=1, deactivated_count=0, sync_run_id=1)

    monkeypatch.setattr("running_contacts.cli.sync_google_contacts", fake_sync_google_contacts)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "contacts",
            "sync",
            "--db-path",
            str(db_path),
            "--token-path",
            str(token_path),
        ],
    )

    assert result.exit_code == 0
    assert captured["credentials_path"] == Path("credentials.json")


def test_contacts_sync_requires_credentials_when_default_is_missing(monkeypatch: object, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["contacts", "sync"])

    assert result.exit_code != 0
    assert "Google OAuth credentials file not found" in result.output


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


def test_race_results_fetch_acn_command(monkeypatch: object, tmp_path: Path) -> None:
    db_path = tmp_path / "race_results.sqlite3"
    raw_dir = tmp_path / "raw"

    def fake_fetch_acn_results(**_: object) -> RaceFetchStats:
        return RaceFetchStats(dataset_id=7, results_count=42)

    monkeypatch.setattr("running_contacts.cli.fetch_acn_results", fake_fetch_acn_results)

    result = runner.invoke(
        app,
        [
            "race-results",
            "fetch-acn",
            "--url",
            "https://www.acn-timing.com/?lng=FR#/events/1/ctx/demo/generic/abc/home/LIVE1",
            "--db-path",
            str(db_path),
            "--raw-dir",
            str(raw_dir),
        ],
    )

    assert result.exit_code == 0
    assert "dataset 7" in result.stdout


def test_race_results_list_datasets_command(tmp_path: Path) -> None:
    db_path = tmp_path / "race_results.sqlite3"
    repository = RaceResultsRepository(db_path)
    repository.initialize()

    result = runner.invoke(app, ["race-results", "list-datasets", "--db-path", str(db_path)])

    assert result.exit_code == 0
    assert "No race datasets found." in result.stdout
