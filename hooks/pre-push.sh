#!/usr/bin/env bash
# hooks/pre-push.sh
#
# Before pushing, runs lint and unit tests and verifies that the spec
# file for the current branch exists in specs/active/.
#
# Install: just hooks

set -euo pipefail

BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
SPEC_ID=$(echo "$BRANCH" | grep -oE 'SPEC-[0-9]+' | head -1 || echo "")

echo ""
echo "  pre-push: running checks on branch '$BRANCH'..."
echo ""

# ── 1. Lint ──────────────────────────────────────────────────────────────────
echo "  [1/3] Linting..."
if ! uv run ruff check . --quiet; then
  echo ""
  echo "  pre-push: lint failed. Run 'just lint' to fix errors before pushing."
  echo ""
  exit 1
fi
echo "        OK"

# ── 2. Unit tests ─────────────────────────────────────────────────────────────
echo "  [2/3] Unit tests..."
if ! uv run pytest -k "not integration" -q --tb=short 2>&1; then
  echo ""
  echo "  pre-push: tests failed. Fix failures before pushing."
  echo ""
  exit 1
fi
echo "        OK"

# ── 3. Spec file check ────────────────────────────────────────────────────────
echo "  [3/3] Spec check..."
if [ -n "$SPEC_ID" ]; then
  SPEC_FILE=$(find specs/active -maxdepth 1 -name "*${SPEC_ID}*" 2>/dev/null | head -1 || echo "")
  if [ -z "$SPEC_FILE" ]; then
    echo ""
    echo "  pre-push: WARNING — no spec file found for $SPEC_ID in specs/active/."
    echo "  Create one from specs/_templates/spec-template.md before pushing."
    echo ""
    # Non-blocking: warn but do not abort push
  else
    STATUS=$(awk '/^---$/{found++; next} found==1 && /^status:/{print $2; exit}' "$SPEC_FILE" | tr -d '"' || echo "")
    echo "        $SPEC_FILE (status: ${STATUS:-unknown})"
  fi
else
  echo "        No SPEC-XXX in branch name — skipped."
fi

echo ""
echo "  pre-push: all checks passed."
echo ""
exit 0
