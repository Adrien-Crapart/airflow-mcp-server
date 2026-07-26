---
name: agent-catalog-hygiene
description: "Keep custom agents, prompts, and skills discoverable and conflict-free in VS Code Copilot. Use for missing agents, duplicate listings, naming collisions, and frontmatter validation."
argument-hint: "Provide symptom (missing or duplicate), expected agent names, and target scope (workspace or personal)."
user-invocable: true
---

# Agent Catalog Hygiene

## Outcome
Resolve discoverability issues for custom agents/prompts/skills and keep the catalog stable.

## When to Use
Use this skill when:
- agents do not appear in chat picker
- the same agent appears multiple times
- slash prompts or skills are not discovered
- frontmatter fields look correct but behavior is inconsistent

## Procedure
1. Validate locations
- Workspace agents must be in .github/agents/*.agent.md
- Workspace skills must be in .github/skills/<name>/SKILL.md
- Workspace prompts should be in .github/prompts/*.prompt.md

2. Validate frontmatter
- name is unique in scope
- description is present and specific
- user-invocable is set intentionally
- for skills, frontmatter name matches folder name

3. Check duplicate sources
- detect same name across workspace/profile/mirror locations
- keep one public name
- set mirror copies to user-invocable: false or remove them

4. Check naming and extension conventions
- agents require .agent.md
- prompts require .prompt.md
- skills require SKILL.md exactly

5. Refresh index
- run Developer: Reload Window in VS Code
- reopen conversation and confirm picker list

6. Document final state
- list public agents/prompts/skills
- record where mirrors are kept and why

## Decision Points
- If agent missing:
  - check file location first, then extension, then frontmatter
- If duplicate appears:
  - check same name across multiple sources
  - rename or hide mirror entries
- If only one conversation is affected:
  - reload window and start a new chat

## Completion Checklist
- [ ] All public agents are in .github/agents/*.agent.md
- [ ] No duplicate public names across sources
- [ ] Skills and prompts follow naming conventions
- [ ] Picker list matches expected catalog
- [ ] Troubleshooting notes captured for maintainers
