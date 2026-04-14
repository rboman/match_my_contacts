from __future__ import annotations

import os
from pathlib import Path

import pytest

from running_contacts.contacts.models import ContactMethod, ContactRecord
from running_contacts.contacts.storage import ContactsRepository
from running_contacts.race_results.models import RaceDataset, RaceResultRow
from running_contacts.race_results.storage import RaceResultsRepository


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QGroupBox, QStatusBar, QTableWidget

from running_contacts_gui.main_window import MainWindow


@pytest.fixture
def qt_app() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_main_window_smoke(qt_app: QApplication, tmp_path: Path) -> None:
    window = MainWindow(
        contacts_db_path=tmp_path / "contacts.sqlite3",
        results_db_path=tmp_path / "race_results.sqlite3",
    )

    assert isinstance(window.findChild(QGroupBox, "contacts_section"), QGroupBox)
    assert isinstance(window.findChild(QGroupBox, "race_results_section"), QGroupBox)
    assert isinstance(window.findChild(QGroupBox, "matching_section"), QGroupBox)
    assert isinstance(window.findChild(QTableWidget, "central_table"), QTableWidget)
    assert isinstance(window.statusBar(), QStatusBar)
    assert window.table.item(0, 0).text() == "No data loaded yet."

    window.close()


def test_load_contacts_populates_table(qt_app: QApplication, tmp_path: Path) -> None:
    contacts_db = build_contacts_db(tmp_path)
    results_db = tmp_path / "race_results.sqlite3"
    window = MainWindow(contacts_db_path=contacts_db, results_db_path=results_db)

    window.contacts_load_button.click()
    qt_app.processEvents()

    assert table_headers(window.table) == ["id", "display_name", "active", "methods", "aliases"]
    assert window.table.rowCount() == 1
    assert window.table.item(0, 1).text() == "Alice Example"
    assert window.table.item(0, 3).text() == "alice@example.com"
    assert window.table.item(0, 4).text() == "Alice Ex"
    assert window.statusBar().currentMessage() == "Loaded 1 contacts."

    window.close()


def test_list_datasets_populates_table(qt_app: QApplication, tmp_path: Path) -> None:
    contacts_db = tmp_path / "contacts.sqlite3"
    results_db = build_race_results_db(tmp_path)
    window = MainWindow(contacts_db_path=contacts_db, results_db_path=results_db)

    window.list_datasets_button.click()
    qt_app.processEvents()

    assert table_headers(window.table) == [
        "id",
        "event_title",
        "event_date",
        "event_location",
        "report",
        "aliases",
        "rows",
    ]
    assert window.table.rowCount() == 1
    assert window.table.item(0, 1).text() == "Demo Race"
    assert window.table.item(0, 5).text() == "demo-race"
    assert window.statusBar().currentMessage() == "Loaded 1 datasets."

    window.close()


def test_show_results_populates_table(qt_app: QApplication, tmp_path: Path) -> None:
    contacts_db = tmp_path / "contacts.sqlite3"
    results_db = build_race_results_db(tmp_path)
    window = MainWindow(contacts_db_path=contacts_db, results_db_path=results_db)
    window.results_dataset_input.setText("demo-race")

    window.show_results_button.click()
    qt_app.processEvents()

    assert table_headers(window.table) == [
        "id",
        "position",
        "athlete_name",
        "finish_time",
        "team",
        "bib",
        "category",
    ]
    assert window.table.rowCount() == 1
    assert window.table.item(0, 2).text() == "Alice Example"
    assert "Showing 1 results for dataset" in window.statusBar().currentMessage()

    window.close()


def test_run_matching_populates_table_and_status(qt_app: QApplication, tmp_path: Path) -> None:
    contacts_db = build_contacts_db(tmp_path)
    results_db = build_race_results_db(tmp_path)
    window = MainWindow(contacts_db_path=contacts_db, results_db_path=results_db)
    window.matching_dataset_input.setText("demo-race")

    window.run_matching_button.click()
    qt_app.processEvents()

    assert table_headers(window.table) == [
        "result_id",
        "athlete_name",
        "contact_name",
        "match_method",
        "score",
        "position",
        "finish_time",
        "team",
        "matched_alias",
    ]
    assert window.table.rowCount() == 1
    assert window.table.item(0, 1).text() == "Alice Example"
    assert window.table.item(0, 2).text() == "Alice Example"
    assert window.statusBar().currentMessage() == "1 accepted, 0 ambiguous, 0 unmatched."

    window.close()


def test_placeholder_action_updates_status_bar(qt_app: QApplication, tmp_path: Path) -> None:
    window = MainWindow(
        contacts_db_path=tmp_path / "contacts.sqlite3",
        results_db_path=tmp_path / "race_results.sqlite3",
    )

    window.contacts_sync_button.click()
    qt_app.processEvents()

    assert window.statusBar().currentMessage() == "Not implemented in GUI yet; use CLI"

    window.close()


def build_contacts_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "contacts.sqlite3"
    repository = ContactsRepository(db_path)
    repository.initialize()
    sync_run_id = repository.begin_sync_run(source="google_people", source_account="default")
    repository.replace_contacts(
        source="google_people",
        source_account="default",
        sync_run_id=sync_run_id,
        contacts=[
            ContactRecord(
                source_contact_id="people/1",
                display_name="Alice Example",
                given_name="Alice",
                family_name="Example",
                methods=[ContactMethod(kind="email", value="alice@example.com")],
                raw_payload={"resourceName": "people/1"},
            )
        ],
    )
    contact_id = int(repository.list_contacts()[0]["id"])
    repository.add_alias(contact_id=contact_id, alias_text="Alice Ex")
    return db_path


def build_race_results_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "race_results.sqlite3"
    repository = RaceResultsRepository(db_path)
    repository.initialize()
    dataset_id = repository.save_dataset(
        dataset=RaceDataset(
            provider="acn_timing",
            source_url="https://example.test",
            external_event_id="1",
            context_db="demo",
            report_key="LIVE1",
            report_path="path",
            event_title="Demo Race",
            event_date="12/04/2026",
            event_location="Liege",
            event_country="BEL",
            total_results=1,
            metadata={},
        ),
        results=[
            RaceResultRow(
                group_name=None,
                group_rank=1,
                position_text="1",
                bib="101",
                athlete_name="Alice Example",
                team="Club A",
                finish_time="0:40:00",
                category="SEF",
                raw_row=["Alice Example"],
            )
        ],
    )
    repository.add_dataset_alias(dataset_id=dataset_id, alias_text="demo-race")
    return db_path


def table_headers(table: QTableWidget) -> list[str]:
    return [table.horizontalHeaderItem(index).text() for index in range(table.columnCount())]
