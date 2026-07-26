# Dossier de preuves QA

Ce dossier stocke les artefacts de validation qualite produits pendant les revues de tickets JIRA/PR.

## Contenu recommande

- Rapports de validation (format section 12 du prompt QA)
- Extraits de sorties de tests unitaires
- Captures de reponses API
- Extraits de logs pertinents (sans donnees sensibles)
- Echantillons de donnees utilises pour verification

## Convention de nommage

Utiliser le format:

`YYYY-MM-DD_<CLE_TICKET>_<ENV>_<TYPE>.md`

Exemples:

- `2026-07-25_PROJ-1234_TESTDEV_rapport.md`
- `2026-07-25_PROJ-1234_TESTDEV_tests-unitaires.md`

## Regles

- Ne jamais stocker de secret (token, mot de passe, cle API).
- Masquer les donnees personnelles si presentes.
- Garder un lien clair entre preuve et critere valide.
