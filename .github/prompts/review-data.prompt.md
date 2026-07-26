---
name: "review-data"
description: "Lance rapidement une review de PR data avec l agent review-dev, format de constats obligatoire et verdict GO/NO-GO evidence-driven."
argument-hint: "Renseigner au minimum: numero/titre PR, commit ou branche, auteur, contexte, criteres d acceptation."
agent: "review-dev"
---

Lance une review complete de PR data avec rapport de conformite, points bloquants, et verdict GO/NO-GO.

Template recommande pour la sortie:
- [PR review report template](../skills/review-evidence-gate/assets/pr-review-report-template.md)

## Formulaire rapide a remplir

- PR_NUMERO: <ex: 248>
- PR_TITRE: <titre de la PR>
- BRANCHE_OU_COMMIT: <branche ou hash court>
- AUTEUR_PR: <nom ou pseudo>
- CONTEXTE_METIER: <objectif fonctionnel>
- TYPE_CONTRIBUTION_PRESUMEE: <pipeline / modele SQL / notebook / modele ML / dashboard / infra / doc>
- CRITERES_ACCEPTATION: <liste breve>
- SOURCES_DE_VERITE: <spec, ticket, data contract, dashboard, etc>
- CONTRAINTES_CONNUES: <SLA, cout, securite, RGPD, AI Act, etc>
- PREUVES_TESTS_DISPONIBLES: <logs CI, commandes, sorties, captures>
- LIMITES_VALIDATION: <ce qui n a pas pu etre teste>

## Consignes d execution

1. Classifier d abord le type de contribution (section 0), puis appliquer uniquement les sections pertinentes.
2. Ne valider un point que s il est verifie dans le diff reel.
3. Pour chaque non-conformite, utiliser le format obligatoire de constat:

   [SEVERITE] <titre court>
   - Preuve: <fichier:ligne ou cellule>
   - Reference: <spec/critere/regle/standard>
   - Risque: <impact>
   - Recommandation: <action concrete et testable>

4. Tout doute securite, confidentialite ou fuite de donnees ML doit etre classe bloquant.
5. Si une section est hors scope, la marquer N/A au niveau section.
6. Si une information manque, ecrire explicitement: Non testable - preuve indisponible.
7. Appliquer les garde-fous qualite specifiques au repo:
   - Controle d acces sur les surfaces d execution tools et operations mutables
   - Exposition des surfaces admin/config sensibles
   - Masquage des donnees sensibles dans ressources/variables
   - Logs 4xx attendus sans stack traces bruyantes
   - Coherence documentation vs CI
   - Distinction integration reelle vs fallback mock/contract
8. Produire le rapport final au format obligatoire de l agent review-dev.
9. Utiliser en priorite le template de sortie recommande.

## Defaults pratiques

- Si PR_NUMERO est vide: utiliser "N/A".
- Si BRANCHE_OU_COMMIT est vide: analyser la branche courante.
- Si TYPE_CONTRIBUTION_PRESUMEE est vide: inferer depuis les fichiers modifies.
- Si des donnees manquent: signaler explicitement les limites dans le rapport.

## Niveaux de severite a utiliser

- BLOQUANT
- RECOMMANDE
- OPTIONNEL
