---
name: review-evidence-gate
description: "Produce strict QA or PR review outputs with mandatory evidence format, severity classification, repository quality gates, and clear GO/NO-GO decision logic."
argument-hint: "Provide PR or ticket id, scope, acceptance criteria, evidence sources, and known limits."
user-invocable: true
---

# Review Evidence Gate

## Outcome
Generate a review decision backed by verifiable evidence and actionable findings.

## When to Use
Use this skill when you need to:
- review a PR with compliance expectations
- produce QA validation with GO/NO-GO
- standardize findings across reviewers

## Related Agents
- review-dev
- qa-reviewer

## Assets Templates
- [QA validation report template](./assets/qa-validation-report-template.md)
- [PR review report template](./assets/pr-review-report-template.md)

## Mandatory Finding Format
Use this exact structure for each finding:

[SEVERITE] <titre court>
- Preuve: <fichier:ligne ou cellule>
- Reference: <spec, critere, regle, standard>
- Risque: <impact si non corrige>
- Recommandation: <action concrete et testable>

If evidence is missing, write exactly:
Non testable - preuve indisponible

## Severity Levels
- BLOQUANT
- RECOMMANDE
- OPTIONNEL

## Procedure
1. Gather scope and evidence sources
- PR/ticket metadata
- changed files and commits
- test/CI outputs
- acceptance criteria and specs

2. Determine applicable sections
- classify contribution type
- mark non-applicable sections as N/A

3. Evaluate repository quality gates
- access control on tool execution surfaces
- sensitive admin/config exposure
- sensitive output masking
- 4xx logging quality
- documentation vs CI consistency
- real integration vs mock fallback evidence

4. Build findings with mandatory format
- one non-compliance per finding
- ensure proof and reference are explicit
- classify severity conservatively for risk

5. Decide GO/NO-GO
- any BLOQUANT unresolved -> NO-GO
- persistent non-testable blocker -> NO-GO
- otherwise GO CONDITIONNEL or GO based on residual risk

6. Produce final report
- section status table
- completion alerts
- findings list
- corrective actions and next step
- use one of the assets templates as the starting structure

## Completion Checklist
- [ ] All findings follow mandatory format
- [ ] Severity levels are consistent with risk
- [ ] Non-testable items explicitly labeled
- [ ] Quality gates are covered
- [ ] Final decision is traceable to evidence
