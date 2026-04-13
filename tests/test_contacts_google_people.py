from __future__ import annotations

from running_contacts.contacts.google_people import person_to_contact_record


def test_person_to_contact_record_maps_primary_fields() -> None:
    person = {
        "resourceName": "people/123",
        "names": [
            {
                "displayName": "Jean-Francois Dupont",
                "givenName": "Jean-Francois",
                "familyName": "Dupont",
                "metadata": {"primary": True},
            }
        ],
        "emailAddresses": [
            {
                "value": "JF.DUPONT@example.com",
                "type": "home",
                "metadata": {"primary": True},
            }
        ],
        "phoneNumbers": [
            {
                "value": "+32 470 12 34 56",
                "type": "mobile",
            }
        ],
        "nicknames": [{"value": "JFD"}],
        "organizations": [{"name": "ACME Running"}],
        "biographies": [{"value": "Known from the running club"}],
    }

    record = person_to_contact_record(person, source_account="main")

    assert record.source_contact_id == "people/123"
    assert record.source_account == "main"
    assert record.display_name == "Jean-Francois Dupont"
    assert record.given_name == "Jean-Francois"
    assert record.family_name == "Dupont"
    assert record.nickname == "JFD"
    assert record.organization == "ACME Running"
    assert record.notes == "Known from the running club"
    assert [(method.kind, method.normalized_value) for method in record.methods] == [
        ("email", "jf.dupont@example.com"),
        ("phone", "+32470123456"),
    ]


def test_person_to_contact_record_handles_sparse_payload() -> None:
    person = {
        "resourceName": "people/999",
        "names": [{"displayName": "Only Name"}],
    }

    record = person_to_contact_record(person)

    assert record.display_name == "Only Name"
    assert record.given_name is None
    assert record.family_name is None
    assert record.methods == []
