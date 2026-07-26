---
name: "debug-airflow"
description: "Diagnostique une erreur Airflow MCP (401/403/404/5xx, timeout, auth, mapping endpoint) et propose un correctif minimal valide."
argument-hint: "Fournir outil en echec, payload, message d erreur exact, contexte local/CI/integration, et preuve de reproduction."
agent: "airflow-debugger"
---

Diagnostique un incident Airflow MCP et produis un plan de correction testable.

## Entrees attendues
- OUTIL_EN_ECHEC: <ex: airflow_dag_run_get>
- PAYLOAD: <params envoyes>
- ERREUR: <message exact + statut HTTP>
- CONTEXTE: <local, CI, integration>
- PREUVES_EXISTANTES: <logs, commandes, captures>

## Procedure attendue
1. Reproduire le probleme.
2. Verifier transport, auth, endpoint cible, mapping d exceptions.
3. Evaluer les quality gates du repo:
   - controle d acces surfaces tools
   - exposition config/admin sensible
   - masquage secrets
   - logs 4xx
   - integration reelle vs fallback mock
4. Identifier la cause racine.
5. Proposer le plus petit correctif possible.
6. Donner les tests ou commandes de validation post-fix.

## Sortie attendue
- Cause racine
- Correctif propose
- Verification post-correctif
- Limites ou hypotheses
