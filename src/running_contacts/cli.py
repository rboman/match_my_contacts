from pathlib import Path

import typer

from running_contacts.contacts.service import sync_google_contacts
from running_contacts.contacts.storage import ContactsRepository
from running_contacts.race_results.service import fetch_acn_results
from running_contacts.race_results.storage import RaceResultsRepository

app = typer.Typer()
contacts_app = typer.Typer(help="Synchroniser et interroger les contacts locaux.")
race_results_app = typer.Typer(help="Recuperer et interroger les resultats de course locaux.")

DEFAULT_DB_PATH = Path("data/contacts.sqlite3")
DEFAULT_TOKEN_PATH = Path("data/google/token.json")
DEFAULT_EXPORT_PATH = Path("data/exports/contacts.json")
DEFAULT_CREDENTIALS_PATH = Path("credentials.json")
DEFAULT_RACE_DB_PATH = Path("data/race_results.sqlite3")
DEFAULT_RACE_RAW_DIR = Path("data/raw/acn_timing")


@app.callback()
def main() -> None:
    """CLI principale de running_contacts."""
    pass

@app.command()
def hello() -> None:
    """Teste que la CLI fonctionne."""
    print("running_contacts OK")


@contacts_app.command("sync")
def contacts_sync(
    credentials_path: Path | None = typer.Option(
        None,
        "--credentials",
        file_okay=True,
        dir_okay=False,
        help="Chemin vers le fichier OAuth client secret Google. Par defaut, utilise ./credentials.json si present.",
    ),
    db_path: Path = typer.Option(
        DEFAULT_DB_PATH,
        "--db-path",
        help="Chemin vers la base SQLite locale.",
    ),
    token_path: Path = typer.Option(
        DEFAULT_TOKEN_PATH,
        "--token-path",
        help="Chemin local pour stocker le token OAuth.",
    ),
    account: str = typer.Option(
        "default",
        "--account",
        help="Nom logique du compte source dans la base locale.",
    ),
) -> None:
    """Synchronise Google Contacts vers SQLite."""
    resolved_credentials_path = credentials_path or DEFAULT_CREDENTIALS_PATH
    if not resolved_credentials_path.exists() or not resolved_credentials_path.is_file():
        raise typer.BadParameter(
            "Google OAuth credentials file not found. "
            "Pass --credentials /path/to/credentials.json or place credentials.json at the repository root."
        )

    stats = sync_google_contacts(
        credentials_path=resolved_credentials_path,
        token_path=token_path,
        db_path=db_path,
        source_account=account,
    )
    typer.echo(
        "Sync completed: "
        f"{stats.fetched_count} fetched, "
        f"{stats.written_count} written, "
        f"{stats.deactivated_count} deactivated."
    )


@contacts_app.command("list")
def contacts_list(
    query: str | None = typer.Option(
        None,
        "--query",
        "-q",
        help="Filtre texte sur le nom, l'email ou le téléphone.",
    ),
    db_path: Path = typer.Option(
        DEFAULT_DB_PATH,
        "--db-path",
        help="Chemin vers la base SQLite locale.",
    ),
    include_inactive: bool = typer.Option(
        False,
        "--include-inactive",
        help="Inclure les contacts absents de la dernière synchronisation.",
    ),
) -> None:
    """Liste les contacts locaux sans appeler Google."""
    repository = ContactsRepository(db_path)
    repository.initialize()
    contacts = repository.list_contacts(query=query, include_inactive=include_inactive)

    if not contacts:
        typer.echo("No contacts found.")
        raise typer.Exit(code=0)

    for contact in contacts:
        methods = ", ".join(method["value"] for method in contact["methods"])
        status = "" if contact["active"] else " [inactive]"
        line = f"{contact['display_name']}{status}"
        if methods:
            line = f"{line} - {methods}"
        typer.echo(line)


@contacts_app.command("export-json")
def contacts_export_json(
    output_path: Path = typer.Option(
        DEFAULT_EXPORT_PATH,
        "--output",
        help="Chemin du fichier JSON d'export.",
    ),
    db_path: Path = typer.Option(
        DEFAULT_DB_PATH,
        "--db-path",
        help="Chemin vers la base SQLite locale.",
    ),
    include_inactive: bool = typer.Option(
        False,
        "--include-inactive",
        help="Inclure les contacts absents de la dernière synchronisation.",
    ),
) -> None:
    """Exporte l'état local des contacts au format JSON."""
    repository = ContactsRepository(db_path)
    repository.initialize()
    export_path = repository.write_export_json(
        output_path=output_path,
        include_inactive=include_inactive,
    )
    typer.echo(f"Exported contacts to {export_path}")


app.add_typer(contacts_app, name="contacts")


@race_results_app.command("fetch-acn")
def race_results_fetch_acn(
    url: str = typer.Option(
        ...,
        "--url",
        help="URL publique ACN Timing de la course ou du tableau de resultats.",
    ),
    db_path: Path = typer.Option(
        DEFAULT_RACE_DB_PATH,
        "--db-path",
        help="Chemin vers la base SQLite locale des resultats.",
    ),
    raw_dir: Path = typer.Option(
        DEFAULT_RACE_RAW_DIR,
        "--raw-dir",
        help="Dossier de snapshots JSON bruts.",
    ),
) -> None:
    """Recupere une course ACN Timing et la stocke localement."""
    stats = fetch_acn_results(url=url, db_path=db_path, raw_dir=raw_dir)
    typer.echo(
        f"Fetched ACN dataset {stats.dataset_id} with {stats.results_count} result rows."
    )


@race_results_app.command("list-datasets")
def race_results_list_datasets(
    db_path: Path = typer.Option(
        DEFAULT_RACE_DB_PATH,
        "--db-path",
        help="Chemin vers la base SQLite locale des resultats.",
    ),
) -> None:
    """Liste les jeux de resultats disponibles localement."""
    repository = RaceResultsRepository(db_path)
    repository.initialize()
    datasets = repository.list_datasets()

    if not datasets:
        typer.echo("No race datasets found.")
        raise typer.Exit(code=0)

    for dataset in datasets:
        typer.echo(
            f"{dataset['id']}: {dataset['event_title']} "
            f"({dataset['event_date']}, {dataset['event_location']}) "
            f"[{dataset['context_db']}/{dataset['report_key']}] "
            f"- {dataset['total_results']} rows"
        )


@race_results_app.command("list-results")
def race_results_list_results(
    dataset_id: int = typer.Option(
        ...,
        "--dataset-id",
        help="Identifiant local du dataset a afficher.",
    ),
    db_path: Path = typer.Option(
        DEFAULT_RACE_DB_PATH,
        "--db-path",
        help="Chemin vers la base SQLite locale des resultats.",
    ),
    query: str | None = typer.Option(
        None,
        "--query",
        "-q",
        help="Filtre texte sur le nom, l'equipe ou le dossard.",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        min=1,
        help="Nombre maximal de lignes a afficher.",
    ),
) -> None:
    """Liste des resultats deja stockes localement."""
    repository = RaceResultsRepository(db_path)
    repository.initialize()
    results = repository.list_results(dataset_id=dataset_id, query=query, limit=limit)

    if not results:
        typer.echo("No race results found.")
        raise typer.Exit(code=0)

    for result in results:
        parts = [
            result["position_text"] or "-",
            result["athlete_name"],
        ]
        if result["finish_time"]:
            parts.append(result["finish_time"])
        if result["team"]:
            parts.append(result["team"])
        if result["bib"]:
            parts.append(f"bib {result['bib']}")
        typer.echo(" | ".join(parts))


@race_results_app.command("export-json")
def race_results_export_json(
    dataset_id: int = typer.Option(
        ...,
        "--dataset-id",
        help="Identifiant local du dataset a exporter.",
    ),
    output_path: Path = typer.Option(
        Path("data/exports/race_results.json"),
        "--output",
        help="Chemin du fichier JSON d'export.",
    ),
    db_path: Path = typer.Option(
        DEFAULT_RACE_DB_PATH,
        "--db-path",
        help="Chemin vers la base SQLite locale des resultats.",
    ),
) -> None:
    """Exporte un dataset de resultats au format JSON."""
    repository = RaceResultsRepository(db_path)
    repository.initialize()
    export_path = repository.write_export_json(dataset_id=dataset_id, output_path=output_path)
    typer.echo(f"Exported race dataset to {export_path}")


app.add_typer(race_results_app, name="race-results")


if __name__ == "__main__":
    app()
