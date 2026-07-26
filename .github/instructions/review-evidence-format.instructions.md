---
description: "Use when writing pull request review comments or review reports. Enforce a strict evidence/reference format for each finding."
applyTo: "**"
---

# Format obligatoire des commentaires de review

Utiliser ce format pour chaque point releve dans une review PR (bloquant, recommande, optionnel).

## Gabarit obligatoire

```text
[SEVERITE] <titre court>
- Preuve: <fichier:ligne ou notebook cellule>
- Reference: <critere d acceptation / spec / regle / standard>
- Risque: <impact si non corrige>
- Recommandation: <action concrete et testable>
```

## Regles de redaction

- Une non-conformite = un commentaire.
- Toujours citer une preuve verifiable (fichier, ligne, cellule, sortie de test).
- Toujours citer la reference qui justifie le constat (spec, checklist, politique, norme).
- Ne jamais laisser un constat sans recommandation concrete.
- Si une information manque, ecrire explicitement: `Non testable - preuve indisponible`.

## Niveaux de severite

- `BLOQUANT`: securite, confidentialite, conformite RGPD/AI Act, fuite de donnees, corruption/perte de donnees, absence de test critique.
- `RECOMMANDE`: dette technique importante, duplication, couverture insuffisante non critique, doc manquante non bloquante.
- `OPTIONNEL`: amelioration de lisibilite ou optimisation mineure sans impact majeur.

## Exemples

```text
[BLOQUANT] Secret expose dans la configuration
- Preuve: airflow_mcp_server/config.py:12
- Reference: Politique securite interne + OWASP Sensitive Data Exposure
- Risque: fuite de credentials et acces non autorise
- Recommandation: retirer le secret du code, utiliser variable d environnement, invalider la cle actuelle
```

```text
[RECOMMANDE] Test manquant sur le chemin de donnees secondaire
- Preuve: tests/unit/test_datasets.py (absence de cas schema invalide)
- Reference: checklist section Tests + criteres d acceptation
- Risque: regression silencieuse sur donnees mal formees
- Recommandation: ajouter un test de validation schema et l executer en CI
```
