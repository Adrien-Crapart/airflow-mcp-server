---
name: "rapport-qa"
description: "Genere automatiquement le rapport de validation qualite (section 12) pour un ticket JIRA/PR data-api, avec constats preuves/references et decision GO/NO-GO stricte."
argument-hint: "Fournir au minimum: CLE_TICKET, TITRE, ENV, DATE_HEURE, resultats des checks (sections 3/5/6/7/8/9/10), alertes, anomalies et recommandation."
agent: "qa-reviewer"
---

Genere un rapport de validation qualite au format section 12.

Template recommande pour la sortie:
- [QA validation report template](../skills/review-evidence-gate/assets/qa-validation-report-template.md)

## Regles obligatoires

- Repondre en francais.
- Ne rien inventer.
- Toute information manquante doit etre marquee "⚠️ Non testable" et produire une alerte de completude.
- Si une preuve manque, ecrire explicitement: "Non testable - preuve indisponible".
- Utiliser uniquement les statuts: ✅, ❌, ⚠️, ➖.
- Lier la recommandation finale (GO / NO-GO / GO CONDITIONNEL) aux preuves disponibles.
- Si un critere bloquant est en ❌ ou ⚠️ persistant, conclure NO-GO.
- Pour chaque anomalie, utiliser le format obligatoire: SEVERITE, Preuve, Reference, Risque, Recommandation.

## Niveaux de severite a utiliser

- BLOQUANT
- RECOMMANDE
- OPTIONNEL

## Garde-fous qualite specifiques au repo

- Verifier la protection des endpoints d execution tools (/tool/{tool_name}, /tool) et des operations mutables.
- Verifier l exposition des capacites admin sensibles (airflow_config_get, airflow://config).
- Verifier le masquage des donnees sensibles dans les ressources/variables.
- Verifier que les erreurs 4xx attendues ne sont pas journalisees avec stacktrace inutile.
- Verifier la coherence doc vs CI (versions runtime/support annoncees vs executees).
- Distinguer explicitement integration reelle vs fallback mock/contract dans les preuves.

## Donnees d'entree attendues

- Metadonnees ticket: cle, titre, PR, environnement, date/heure du passage.
- Resultats par section: 3, 5, 6, 7, 8, 9, 10.x.
- Liste des alertes de completude.
- Liste des anomalies detectees avec severite + preuve + reference + risque + recommandation.
- Actions correctives, responsables et delais.

## Sortie attendue

Produire exactement ce format, rempli avec les informations disponibles:

```text
RAPPORT DE VALIDATION QUALITE
==============================
Ticket JIRA             : {{CLE_TICKET}} - {{TITRE}}
Date / heure du passage : {{DATE_HEURE}}
Environnement teste     : {{TESTDEV / PREPROD / PRODUCTION}}
Agent / testeur         : {{NOM}}

1. SYNTHESE
   - Taux de completude du ticket (section 3)       : {{X}} / 12 elements presents
   - Taux de couverture des cas de test (section 9) : {{X}} %
   - Nombre d'alertes de completude declenchees     : {{N}}
   - Nombre d'anomalies detectees                   : {{N}}
   - Recommandation finale                          : {{GO / NO-GO / GO CONDITIONNEL}}

2. DETAIL PAR SECTION
   | Section                          | Statut global | Points bloquants |
   |----------------------------------|---------------|------------------|
   | 3. Completude du ticket          |               |                  |
   | 5. Qualite technique             |               |                  |
   | 6. Qualite metier/fonctionnelle  |               |                  |
   | 7. Qualite des donnees           |               |                  |
   | 8. Qualite API                   |               |                  |
   | 9. Cas de test                   |               |                  |
   | 10.x Environnement teste         |               |                  |

3. ALERTES DE COMPLETUDE DECLENCHEES
   - {{Liste des alertes au format modele section 3}}

4. ANOMALIES DETECTEES
   [SEVERITE] {{Titre court}}
   - Preuve: {{fichier:ligne ou cellule}}
   - Reference: {{spec/critere/regle/standard}}
   - Risque: {{impact si non corrige}}
   - Recommandation: {{action concrete et testable}}
   (Repeter ce bloc pour chaque anomalie)

5. ACTIONS CORRECTIVES REQUISES AVANT LA PROCHAINE ETAPE
   - {{Action 1 - responsable - delai}}
   - {{Action 2 - responsable - delai}}

6. PROCHAINE ETAPE
   - {{Rejouer sur environnement suivant / Corriger et rejouer / Cloturer ticket}}
```

## Comportement si donnees manquantes

- Ne pas supprimer de section.
- Renseigner "⚠️ Non testable" dans les champs concernes.
- Ajouter explicitement les alertes dans la section 3 du rapport.
