from pathlib import Path

import typer

from running_contacts.contacts.service import sync_google_contacts
from running_contacts.contacts.storage import ContactsRepository

app = typer.Typer()
contacts_app = typer.Typer(help="Synchroniser et interroger les contacts locaux.")

DEFAULT_DB_PATH = Path("data/contacts.sqlite3")
DEFAULT_TOKEN_PATH = Path("data/google/token.json")
DEFAULT_EXPORT_PATH = Path("data/exports/contacts.json")


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
    credentials_path: Path = typer.Option(
        ...,
        "--credentials",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Chemin vers le fichier OAuth client secret Google.",
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
    stats = sync_google_contacts(
        credentials_path=credentials_path,
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


if __name__ == "__main__":
    app()
