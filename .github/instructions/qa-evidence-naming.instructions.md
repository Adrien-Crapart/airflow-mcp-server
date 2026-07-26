---
description: "Use when updating QA evidence documentation in docs/qa-evidence/README.md. Enforce the naming convention for QA proof files before sharing with reviewers."
applyTo: "docs/qa-evidence/README.md"
---

# Regles de nommage des preuves QA

Utiliser obligatoirement ce format pour chaque preuve:

`YYYY-MM-DD_<CLE_TICKET>_<ENV>_<TYPE>.md`

## Regles

- `YYYY-MM-DD`: date ISO du passage QA.
- `<CLE_TICKET>`: cle JIRA en majuscules, format type `PROJ-1234`.
- `<ENV>`: uniquement `TESTDEV`, `PREPROD`, ou `PRODUCTION`.
- `<TYPE>`: type de preuve en minuscules kebab-case (ex: `rapport`, `tests-unitaires`, `logs-api`, `donnees-echantillon`).
- Extension obligatoire: `.md`.
- Interdits: espaces, accents, caracteres speciaux hors `-` et `_`.

## Validation rapide

Verifier que le nom correspond a cette regex:

`^\d{4}-\d{2}-\d{2}_[A-Z][A-Z0-9]+-\d+_(TESTDEV|PREPROD|PRODUCTION)_[a-z0-9-]+\.md$`

## Exemples valides

- `2026-07-25_PROJ-1234_TESTDEV_rapport.md`
- `2026-07-25_PROJ-1234_PREPROD_tests-unitaires.md`
- `2026-07-25_PROJ-1234_PRODUCTION_logs-api.md`

## Action en cas d'ecart

- Renommer le fichier pour respecter le format.
- Mettre a jour les liens references dans la documentation QA si necessaire.
