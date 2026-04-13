# running_contacts

Outil local-first pour centraliser des contacts, importer des résultats de course, puis croiser les deux sans dépendre à chaque fois des sources externes.

## Problème visé

Après une course avec plusieurs milliers de participants, l’objectif est de répondre rapidement à la question: quels contacts ont participé, et quel est leur résultat ? Le projet est pensé dès le départ comme trois briques indépendantes et réutilisables:

1. `contacts`: importer et stocker les contacts localement.
2. `race_results`: récupérer et normaliser les résultats d’une course.
3. `matching`: croiser les données déjà stockées et produire un tableau exploitable.

Une extension envisagée ensuite est l’analyse de documents longs, par exemple des PDF de réunions, pour retrouver les passages qui mentionnent certains contacts.

## Choix d’architecture

- Source de vérité locale: SQLite.
- Exports secondaires: JSON/CSV selon les besoins.
- Code organisé par domaines réutilisables, pas comme un seul script.
- Projet local, sans backend distant.
- Pas d’ORM en première intention: `sqlite3` suffit.

## État actuel

La première brique `contacts` est en place pour un compte Google:

- OAuth Desktop via Google People API.
- Synchronisation complète réexécutable vers `data/contacts.sqlite3`.
- Consultation locale sans appel réseau.
- Export JSON de l’état local.

Le stockage local repose sur trois tables:

- `contacts`
- `contact_methods`
- `sync_runs`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Préparer l’accès Google Contacts

1. Créer un projet Google Cloud.
2. Activer Google People API.
3. Créer des identifiants OAuth pour une application Desktop.
4. Télécharger le fichier `credentials.json`.

Le fichier d’identifiants peut rester hors du dépôt. Le token OAuth généré par la CLI est stocké localement sous `data/google/token.json` par défaut.
Si `credentials.json` est présent à la racine du dépôt, la commande de sync l’utilise automatiquement.

## Commandes utiles

Tester la CLI:

```bash
running-contacts hello
```

Synchroniser les contacts Google vers SQLite:

```bash
running-contacts contacts sync
running-contacts contacts sync --credentials /chemin/vers/credentials.json
```

Lister les contacts locaux:

```bash
running-contacts contacts list
running-contacts contacts list --query dupont
```

Exporter l’état local en JSON:

```bash
running-contacts contacts export-json --output data/exports/contacts.json
```

Lancer les tests:

```bash
pytest -q
```

## Roadmap courte

1. Stabiliser la brique `contacts`.
2. Ajouter un connecteur `race_results` pour ACN Timing.
3. Introduire la normalisation et le matching de noms.
4. Produire une sortie terminal/CSV, puis éventuellement une petite UI locale.
