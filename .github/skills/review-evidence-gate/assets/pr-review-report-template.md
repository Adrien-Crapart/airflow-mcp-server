# PR Review Report Template

# Rapport de Review - PR #{{PR_NUMERO}} - {{PR_TITRE}}

Date de la review : {{DATE}}
Agent/modele utilise : GPT-5.3-Codex
Commit analyse : {{COMMIT_COURT}}
Auteur de la PR : {{AUTEUR}}
Type de contribution : {{pipeline / modele SQL / notebook / modele ML / dashboard / infra / doc}}

## Verdict global
- [ ] Approuve
- [ ] Approuve avec reserves
- [ ] Changements requis
- [ ] Rejete (risque critique data, confidentialite ou conformite)

## Score de conformite
- Points verifies : {{X}} / {{Y}}
- Points conformes : {{X}} ({{Z}} %)
- Points non applicables : {{N}}

## Points bloquants (a corriger avant merge)
[BLOQUANT] {{TITRE_COURT}}
- Preuve: {{fichier:ligne ou cellule}}
- Reference: {{spec, critere, regle, standard}}
- Risque: {{impact si non corrige}}
- Recommandation: {{action concrete et testable}}

## Ameliorations recommandees
[RECOMMANDE] {{TITRE_COURT}}
- Preuve: {{fichier:ligne ou cellule}}
- Reference: {{spec, critere, regle, standard}}
- Risque: {{impact si non corrige}}
- Recommandation: {{action concrete et testable}}

## Suggestions optionnelles
[OPTIONNEL] {{TITRE_COURT}}
- Preuve: {{fichier:ligne ou cellule}}
- Reference: {{spec, critere, regle, standard}}
- Risque: {{impact si non corrige}}
- Recommandation: {{action concrete et testable}}

## Detail par section de la checklist
| Section | Conforme | Non conforme | N/A | Commentaire |
|---|---|---|---|---|
| Qualite et bonnes pratiques | | | | |
| Architecture et modelisation des donnees | | | | |
| Qualite et fiabilite des donnees | | | | |
| Securite et confidentialite (RGPD) | | | | |
| Data Science / ML | | | | |
| Performance, cout et fiabilite | | | | |
| Tests | | | | |
| Documentation | | | | |
| Git / CI-CD | | | | |

## Synthese
{{2-3 phrases sur l etat general et la decision recommandee}}

## Regles de decision
- Si un BLOQUANT est non resolu: Changements requis ou Rejete
- Si une preuve critique manque: Non testable - preuve indisponible
- Ne jamais downgraded un risque securite/confidentialite/leakage en optionnel
