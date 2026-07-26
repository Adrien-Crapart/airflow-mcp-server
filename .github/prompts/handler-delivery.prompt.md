---
name: "handler-delivery"
description: "Construit ou modifie un handler MCP Airflow avec schema, enregistrement, quality gates et tests minimaux obligatoires."
argument-hint: "Fournir domaine, action, endpoint Airflow cible, params d entree, et si l action est read-only ou mutante."
agent: "handler-developer"
---

Implante un changement de handler MCP de bout en bout avec verification qualite.

## Entrees attendues
- DOMAINE: <ex: dags, tasks, variables>
- ACTION: <ex: list, get, trigger, delete>
- ENDPOINT_AIRFLOW: <ex: /api/v2/dags/{dag_id}>
- PARAMS_ENTREE: <schema attendu>
- TYPE_OPERATION: <read-only / mutante>
- CONTRAINTES_SECURITE: <sensitive data, masking, droits>

## Exigences
1. Valider les params via Pydantic model_validate.
2. Respecter strictement le contrat de reponse success/data/error.
3. Enregistrer le handler dans TOOLS et le schema dans TOOL_INPUT_MODELS.
4. Si operation mutante: maj WRITE_ONLY_TOOLS et verifier MCP_READ_ONLY.
5. Ajouter ou mettre a jour les tests unitaires: succes, param manquant, 404, 503, 401.
6. Mettre a jour la documentation si le comportement outillage evolue.

## Sortie attendue
- Liste des fichiers modifies
- Diff ou resume des changements
- Commandes de verification executees
- Risques residuels et prochaines actions
