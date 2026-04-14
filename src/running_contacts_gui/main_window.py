from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from running_contacts.contacts.storage import ContactsRepository
from running_contacts.matching.service import match_dataset
from running_contacts.race_results.storage import RaceResultsRepository

from .table_presenter import TablePresenter


DEFAULT_CONTACTS_DB_PATH = Path("data/contacts.sqlite3")
DEFAULT_RESULTS_DB_PATH = Path("data/race_results.sqlite3")
DEFAULT_RESULTS_LIMIT = 100


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        contacts_db_path: Path = DEFAULT_CONTACTS_DB_PATH,
        results_db_path: Path = DEFAULT_RESULTS_DB_PATH,
    ) -> None:
        super().__init__()
        self.contacts_db_path = Path(contacts_db_path)
        self.results_db_path = Path(results_db_path)

        self.setWindowTitle("running_contacts")
        self.resize(1100, 700)

        self.contacts_query_input = QLineEdit()
        self.results_dataset_input = QLineEdit()
        self.matching_dataset_input = QLineEdit()

        self.contacts_load_button = QPushButton("Load contacts")
        self.contacts_sync_button = QPushButton("Sync (CLI for now)")
        self.list_datasets_button = QPushButton("List datasets")
        self.show_results_button = QPushButton("Show results")
        self.fetch_acn_button = QPushButton("Fetch ACN (CLI for now)")
        self.run_matching_button = QPushButton("Run matching")
        self.export_review_button = QPushButton("Export/Review (CLI for now)")

        self.table = QTableWidget()
        self.table.setObjectName("central_table")
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table_presenter = TablePresenter(self.table)

        central_widget = QWidget()
        layout = QHBoxLayout(central_widget)
        controls_layout = QVBoxLayout()
        controls_layout.addWidget(self._build_contacts_section())
        controls_layout.addWidget(self._build_race_results_section())
        controls_layout.addWidget(self._build_matching_section())
        controls_layout.addStretch(1)

        layout.addLayout(controls_layout, stretch=0)
        layout.addWidget(self.table, stretch=1)
        self.setCentralWidget(central_widget)

        self.setStatusBar(QStatusBar(self))
        self.table_presenter.show_placeholder("No data loaded yet.")
        self.statusBar().showMessage("GUI ready.")

        self.contacts_load_button.clicked.connect(self.load_contacts)
        self.contacts_sync_button.clicked.connect(self.show_placeholder_message)
        self.list_datasets_button.clicked.connect(self.list_datasets)
        self.show_results_button.clicked.connect(self.show_results)
        self.fetch_acn_button.clicked.connect(self.show_placeholder_message)
        self.run_matching_button.clicked.connect(self.run_matching)
        self.export_review_button.clicked.connect(self.show_placeholder_message)

    def _build_contacts_section(self) -> QGroupBox:
        section = QGroupBox("Contacts")
        section.setObjectName("contacts_section")
        layout = QVBoxLayout(section)

        self.contacts_query_input.setPlaceholderText("Search by name, email, or phone")
        layout.addWidget(self.contacts_query_input)
        layout.addWidget(self.contacts_load_button)
        layout.addWidget(self.contacts_sync_button)
        return section

    def _build_race_results_section(self) -> QGroupBox:
        section = QGroupBox("Race Results")
        section.setObjectName("race_results_section")
        layout = QVBoxLayout(section)

        self.results_dataset_input.setPlaceholderText("Dataset id or alias")
        layout.addWidget(self.results_dataset_input)
        layout.addWidget(self.list_datasets_button)
        layout.addWidget(self.show_results_button)
        layout.addWidget(self.fetch_acn_button)
        return section

    def _build_matching_section(self) -> QGroupBox:
        section = QGroupBox("Matching")
        section.setObjectName("matching_section")
        layout = QVBoxLayout(section)

        self.matching_dataset_input.setPlaceholderText("Dataset id or alias")
        layout.addWidget(self.matching_dataset_input)
        layout.addWidget(self.run_matching_button)
        layout.addWidget(self.export_review_button)
        return section

    def load_contacts(self) -> None:
        try:
            repository = ContactsRepository(self.contacts_db_path)
            repository.initialize()
            query = self._clean_text(self.contacts_query_input.text())
            contacts = repository.list_contacts(query=query)
            self.table_presenter.show_contacts(contacts)
            self.statusBar().showMessage(f"Loaded {len(contacts)} contacts.")
        except Exception as exc:
            self._show_error(exc)

    def list_datasets(self) -> None:
        try:
            repository = RaceResultsRepository(self.results_db_path)
            repository.initialize()
            datasets = repository.list_datasets()
            self.table_presenter.show_datasets(datasets)
            self.statusBar().showMessage(f"Loaded {len(datasets)} datasets.")
        except Exception as exc:
            self._show_error(exc)

    def show_results(self) -> None:
        try:
            selector = self._require_dataset_selector(self.results_dataset_input)
            repository = RaceResultsRepository(self.results_db_path)
            repository.initialize()
            dataset_id = repository.resolve_dataset_selector(selector)
            results = repository.list_results(dataset_id=dataset_id, limit=DEFAULT_RESULTS_LIMIT)
            self.table_presenter.show_race_results(results)
            self.statusBar().showMessage(
                f"Showing {len(results)} results for dataset {dataset_id}."
            )
        except Exception as exc:
            self._show_error(exc)

    def run_matching(self) -> None:
        try:
            selector = self._require_dataset_selector(self.matching_dataset_input)
            repository = RaceResultsRepository(self.results_db_path)
            repository.initialize()
            dataset_id = repository.resolve_dataset_selector(selector)
            report = match_dataset(
                contacts_db_path=self.contacts_db_path,
                results_db_path=self.results_db_path,
                dataset_id=dataset_id,
            )
            self.table_presenter.show_matches(report)
            self.statusBar().showMessage(
                f"{len(report.accepted_matches)} accepted, "
                f"{len(report.ambiguous_matches)} ambiguous, "
                f"{report.unmatched_count} unmatched."
            )
        except Exception as exc:
            self._show_error(exc)

    def show_placeholder_message(self) -> None:
        self.statusBar().showMessage("Not implemented in GUI yet; use CLI")

    def _require_dataset_selector(self, field: QLineEdit) -> str:
        selector = self._clean_text(field.text())
        if selector is None:
            raise ValueError("Enter a dataset id or alias first.")
        return selector

    @staticmethod
    def _clean_text(value: str) -> str | None:
        cleaned = value.strip()
        return cleaned or None

    def _show_error(self, exc: Exception) -> None:
        self.statusBar().showMessage(f"Error: {exc}")
