---
name: "write-handler-tests"
description: "Genere ou met a jour les tests unitaires d un handler MCP Airflow avec scenarios obligatoires et preuves d execution."
argument-hint: "Fournir le handler cible, les changements effectues, et les erreurs/situations a couvrir."
agent: "test-writer"
---

Ecris les tests unitaires pour un handler en respectant les regles du projet.

## Entrees attendues
- HANDLER_CIBLE: <fichier et fonction>
- CHANGEMENTS_FONCTIONNELS: <ce qui a ete ajoute/modifie>
- CAS_CRITIQUES: <erreurs ou regressions connues>

## Scenarios obligatoires
1. Nominal succes
2. Parametre requis manquant
3. AirflowNotFoundError
4. AirflowConnectionError
5. AirflowAuthError

## Scenarios qualite additionnels (si pertinent)
- read-only mode cache les outils mutables
- masquage des donnees sensibles
- distinction integration reelle vs fallback mock

## Contraintes
- Utiliser monkeypatch.setattr sur airflow_client
- Marquer les coroutines avec pytest.mark.asyncio
- Respecter le naming test_<action>_<scenario>

## Sortie attendue
- Fichiers de tests modifies
- Couverture des scenarios (checklist)
- Commandes lancees et resultat
