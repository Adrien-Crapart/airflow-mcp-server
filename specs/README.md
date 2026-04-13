# Specs

Feature and change specifications for the Airflow MCP Server.

## Folder structure

| Folder | Purpose |
| --- | --- |
| `_templates/` | Blank templates to copy when starting a new spec |
| `active/` | Specs currently in development — one per branch |
| `domain/` | Stable domain reference docs (DAGs, tasks, connections…) — not tied to a branch |
| `done/` | Completed specs (moved automatically by the `post-merge` hook) |
| `wireframes/` | Flow diagrams, sequence diagrams, mockups |

## Naming convention

```
SPEC-{id}-{slug}.md
```

Examples: `SPEC-001-add-xcom-tool.md`, `SPEC-042-airflow3-migration.md`

## Branch convention

```
feature/SPEC-{id}-{slug}
fix/SPEC-{id}-{slug}
```

The git hooks read the branch name to extract `SPEC-{id}` automatically.

## Lifecycle

```
_templates/spec-template.md
        ↓  (copy + fill in)
active/SPEC-{id}-{slug}.md        ← set status: active
        ↓  (work done, set status: done)
done/SPEC-{id}-{slug}.md          ← moved by post-merge hook
```

## Install git hooks

```bash
just hooks
```
