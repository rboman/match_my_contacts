# Handoff Notes

Read this file first when resuming work on `running_contacts` in a later Codex session.

## Current State

- `contacts` is implemented and syncs one Google account into `data/contacts.sqlite3`.
- `race_results` is implemented for ACN Timing / Chronorace and stores local datasets in `data/race_results.sqlite3`.
- `matching` is implemented with:
  - exact and fuzzy matching,
  - contact aliases,
  - race dataset aliases,
  - manual review commands (`accept`, `reject`, `clear-review`, `list-reviews`),
  - sorted and filtered listing (`matching list`).
- a first desktop GUI is now the intended next product step, on top of the existing local-first workflow.

## Important Local Selectors

- Main imported race dataset:
  - `dataset_id = 1`
  - alias: `liege-15k-2026`

## Known Current Result

At the time of this handoff, running:

```bash
running-contacts matching run --dataset liege-15k-2026
```

returns approximately:

- `47 accepted matches`
- `0 ambiguous`

This can evolve if contacts are resynced or aliases/reviews are changed.

## Manual Cleanup Already Applied

- Added contact alias:
  - contact `972` (`Pierre-Paul Jeunechamps`) -> alias `Pierre Jeunechamps`

Reason:
- this resolved the previous ambiguous race result `JEUNECHAMPS Pierre`.

## Useful Commands

Sync contacts:

```bash
running-contacts contacts sync
```

Inspect contacts and aliases:

```bash
running-contacts contacts list --query noel
running-contacts contacts list-aliases
```

Inspect races:

```bash
running-contacts race-results list-datasets
running-contacts race-results list-aliases
running-contacts race-results list-results --dataset liege-15k-2026 --query ucci
```

Inspect matches:

```bash
running-contacts matching run --dataset liege-15k-2026 --include-ambiguous --limit 30
running-contacts matching list --dataset liege-15k-2026 --team TEAMULIEGE --sort time
running-contacts matching list --dataset liege-15k-2026 --status all --sort athlete
```

Manual corrections:

```bash
running-contacts contacts add-alias --contact-id 691 --alias "Jean Noel"
running-contacts matching accept --dataset liege-15k-2026 --result-id 1234 --contact-id 691
running-contacts matching reject --dataset liege-15k-2026 --result-id 5678 --note "homonyme"
running-contacts matching list-reviews --dataset liege-15k-2026
```

## How To Resume Codex

Resume the most recent interactive Codex session:

```bash
codex resume --last
```

Open the session picker:

```bash
codex resume
```

If you do not resume the exact same interactive session, start the new session in this repo and point it to:

```bash
README.md
USAGE.md
HANDOFF.md
```

## Recommended Next Work

Most likely next step:

- add a minimal local desktop GUI in PySide6 while keeping the CLI and core logic unchanged

Why this is the next step:

1. the current matching is considered satisfactory for now
2. the project already has useful local workflows worth exposing graphically
3. a simple GUI can improve day-to-day usability without changing the core services

Initial GUI scope:

1. `Contacts` section
2. `Race Results` section
3. `Matching` section
4. central table
5. status bar

Run the GUI locally with:

```bash
pip install -e .[gui]
sudo apt install libxcb-cursor0  # if needed on Linux/X11
running-contacts-gui
```
