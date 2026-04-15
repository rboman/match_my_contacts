"""Contacts synchronization and local storage."""

from .models import ContactMethod, ContactRecord, SyncStats
from .service import sync_google_contacts
from .storage import ContactsRepository

__all__ = [
    "ContactMethod",
    "ContactRecord",
    "ContactsRepository",
    "SyncStats",
    "sync_google_contacts",
]
