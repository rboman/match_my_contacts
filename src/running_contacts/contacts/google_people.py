from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ContactMethod, ContactRecord
from .normalization import normalize_email, normalize_phone

SCOPES = ["https://www.googleapis.com/auth/contacts.readonly"]


def fetch_google_contacts(
    *,
    credentials_path: Path,
    token_path: Path,
    source_account: str = "default",
) -> list[ContactRecord]:
    creds = _load_credentials(credentials_path=credentials_path, token_path=token_path)
    service = _build_people_service(creds)
    people = _fetch_people_pages(service)
    return [person_to_contact_record(person, source_account=source_account) for person in people]


def _load_credentials(*, credentials_path: Path, token_path: Path) -> Any:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise RuntimeError(
            "Google client dependencies are missing. Install the project dependencies "
            "before running `running-contacts contacts sync`."
        ) from exc

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _build_people_service(creds: Any) -> Any:
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google API client is missing. Install the project dependencies before syncing contacts."
        ) from exc

    return build("people", "v1", credentials=creds, cache_discovery=False)


def _fetch_people_pages(service: Any) -> list[dict[str, Any]]:
    people: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        response = (
            service.people()
            .connections()
            .list(
                resourceName="people/me",
                pageSize=1000,
                pageToken=page_token,
                personFields=(
                    "names,emailAddresses,phoneNumbers,nicknames,"
                    "organizations,biographies,metadata"
                ),
            )
            .execute()
        )
        people.extend(response.get("connections", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            return people


def person_to_contact_record(person: dict[str, Any], *, source_account: str = "default") -> ContactRecord:
    names = person.get("names", [])
    primary_name = _pick_primary_entry(names)

    display_name = (
        primary_name.get("displayName")
        or " ".join(
            part for part in [primary_name.get("givenName"), primary_name.get("familyName")] if part
        ).strip()
        or person.get("resourceName", "unknown-contact")
    )

    methods: list[ContactMethod] = []
    methods.extend(_extract_email_methods(person.get("emailAddresses", [])))
    methods.extend(_extract_phone_methods(person.get("phoneNumbers", [])))

    biography = _pick_primary_entry(person.get("biographies", []))
    organization = _pick_primary_entry(person.get("organizations", []))
    nickname = _pick_primary_entry(person.get("nicknames", []))

    return ContactRecord(
        source_contact_id=person["resourceName"],
        source_account=source_account,
        display_name=display_name,
        given_name=primary_name.get("givenName"),
        family_name=primary_name.get("familyName"),
        nickname=nickname.get("value"),
        organization=organization.get("name"),
        notes=biography.get("value"),
        methods=methods,
        raw_payload=json.loads(json.dumps(person)),
    )


def _extract_email_methods(entries: list[dict[str, Any]]) -> list[ContactMethod]:
    methods: list[ContactMethod] = []
    for entry in entries:
        value = (entry.get("value") or "").strip()
        if not value:
            continue
        methods.append(
            ContactMethod(
                kind="email",
                value=value,
                label=entry.get("formattedType") or entry.get("type"),
                normalized_value=normalize_email(value),
                is_primary=_is_primary(entry),
            )
        )
    return methods


def _extract_phone_methods(entries: list[dict[str, Any]]) -> list[ContactMethod]:
    methods: list[ContactMethod] = []
    for entry in entries:
        value = (entry.get("value") or "").strip()
        if not value:
            continue
        methods.append(
            ContactMethod(
                kind="phone",
                value=value,
                label=entry.get("formattedType") or entry.get("type"),
                normalized_value=normalize_phone(value),
                is_primary=_is_primary(entry),
            )
        )
    return methods


def _is_primary(entry: dict[str, Any]) -> bool:
    metadata = entry.get("metadata", {})
    return bool(metadata.get("primary")) or bool(metadata.get("sourcePrimary"))


def _pick_primary_entry(entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        return {}
    for entry in entries:
        if _is_primary(entry):
            return entry
    return entries[0]
