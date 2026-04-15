from __future__ import annotations

from match_my_contacts.race_results.acn import (
    AcnFetchedPayload,
    build_dataset,
    parse_acn_url,
)


def test_parse_acn_url_extracts_expected_identifiers() -> None:
    descriptor = parse_acn_url(
        "https://www.acn-timing.com/?lng=FR#/events/2157220339092161/ctx/20260412_liege/generic/197994_1/home/LIVE1"
    )

    assert descriptor.event_id == "2157220339092161"
    assert descriptor.context_db == "20260412_liege"
    assert descriptor.report_path == "197994_1"
    assert descriptor.report_key == "LIVE1"


def test_build_dataset_normalizes_core_result_fields() -> None:
    descriptor = parse_acn_url(
        "https://www.acn-timing.com/?lng=FR#/events/2157220339092161/ctx/20260412_liege/generic/197994_1/home/LIVE1"
    )
    payload = AcnFetchedPayload(
        descriptor=descriptor,
        event_payload={
            "EventId": 2157220339092161,
            "Title": "Ethias 15km de Liege Metropole",
            "Date": "12/04/2026",
            "Location": "Liege",
            "Country": "BEL",
            "Parameters": {"db": "20260412_liege"},
        },
        results_payload={
            "Count": 1,
            "Settings": {"Live": True},
            "TableDefinition": {
                "Columns": [
                    {"FieldIdx": 0, "Name": "sR_Pos", "DisplayName": "Pos"},
                    {"FieldIdx": 1, "Name": "sI_w500_#NR", "DisplayName": "#NR"},
                    {"FieldIdx": 2, "Name": "sB_#NAME", "DisplayName": "#NAME"},
                    {"FieldIdx": 3, "Name": "w700_#TEAM", "DisplayName": "#TEAM"},
                    {"FieldIdx": 4, "Name": "dNat_sC_#NOC", "DisplayName": "#NOC"},
                    {"FieldIdx": 5, "Name": "sH_#GENDER", "DisplayName": "#GENDER"},
                    {"FieldIdx": 9, "Name": "sC_#LOCATION", "DisplayName": "#LOCATION"},
                    {"FieldIdx": 10, "Name": "sBR_#TIME", "DisplayName": "#TIME"},
                    {"FieldIdx": 12, "Name": "w700_sR_#AVG", "DisplayName": "#AVG"},
                    {
                        "FieldIdx": 13,
                        "Name": "gCateg_sR_Rang",
                        "DisplayName": "Rang",
                        "GroupDisplayName": "Categ",
                    },
                    {"FieldIdx": 14, "Name": "gCateg_w700_#CAT", "DisplayName": "#CAT"},
                    {"FieldIdx": 15, "Name": "sH_RowAction", "DisplayName": "RowAction"},
                    {"FieldIdx": 16, "Name": "sH_RowClass", "DisplayName": "RowClass"},
                ]
            },
            "Groups": [
                {
                    "Id": "",
                    "Name": None,
                    "SlaveRows": [
                        [
                            "1.",
                            "43499",
                            "PAQUET Amaury",
                            "BMW DELBECQ",
                            "BEL",
                            "M",
                            "",
                            "",
                            "",
                            "Finish",
                            "0:47:45",
                            "-",
                            "19.219",
                            "1",
                            "SEH",
                            "detail:43499_1",
                            "",
                        ]
                    ],
                }
            ],
        },
    )

    dataset, rows = build_dataset(payload)

    assert dataset.event_title == "Ethias 15km de Liege Metropole"
    assert dataset.total_results == 1
    assert rows[0].athlete_name == "PAQUET Amaury"
    assert rows[0].bib == "43499"
    assert rows[0].finish_time == "0:47:45"
    assert rows[0].category == "SEH"
    assert rows[0].detail_token == "43499_1"
