---
name: "catalog-hygiene"
description: "Corrige les problemes de detection des customizations Copilot (agents, prompts, skills): absents, dupliques, collisions de noms."
argument-hint: "Fournir le symptome observe, les noms attendus, et si le probleme est workspace ou profil utilisateur."
agent: "agent"
---

Diagnostique et corrige un probleme de catalogue de customizations.

## Entrees attendues
- SYMPTOME: <non detecte, liste en double, mauvais agent>
- CIBLES_ATTENDUES: <noms agents/prompts/skills>
- SCOPE: <workspace ou user profile>

## Procedure attendue
1. Verifier emplacement et extension:
   - agents: .github/agents/*.agent.md
   - prompts: .github/prompts/*.prompt.md
   - skills: .github/skills/<name>/SKILL.md
2. Verifier frontmatter: name unique, description, user-invocable.
3. Identifier doublons multi-sources et decider une source publique unique.
4. Corriger collisions (rename/hide miroir).
5. Proposer un reload VS Code pour rafraichir l index.

## Sortie attendue
- Cause du probleme
- Correctifs appliques
- Liste finale des customizations detectables
- Etape de verification utilisateur
