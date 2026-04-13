#!/usr/bin/env bash
# hooks/prepare-commit-msg.sh
#
# Prepends the SPEC-XXX identifier extracted from the current branch name
# to the commit message draft. Skips merge, squash, and amend commits.
#
# Install: just hooks

set -euo pipefail

COMMIT_MSG_FILE="$1"
COMMIT_SOURCE="${2:-}"

# Skip automated commits (merge, squash, amend, etc.)
case "$COMMIT_SOURCE" in
  merge|squash|commit) exit 0 ;;
esac

# Extract SPEC-XXX from branch name (e.g. feature/SPEC-042-add-xcom → SPEC-042)
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
SPEC_ID=$(echo "$BRANCH" | grep -oE 'SPEC-[0-9]+' | head -1 || echo "")

if [ -z "$SPEC_ID" ]; then
  exit 0
fi

CURRENT_MSG=$(cat "$COMMIT_MSG_FILE")

# Do not add twice
if echo "$CURRENT_MSG" | grep -qF "$SPEC_ID"; then
  exit 0
fi

# Find the spec file in active/ to retrieve its title
SPEC_FILE=$(find specs/active -maxdepth 1 -name "*${SPEC_ID}*" 2>/dev/null | head -1 || echo "")
SPEC_TITLE=""
if [ -n "$SPEC_FILE" ]; then
  SPEC_TITLE=$(grep -m1 '^title:' "$SPEC_FILE" | sed 's/^title: *//' | tr -d '"' || echo "")
fi

# Append refs footer
{
  echo "$CURRENT_MSG"
  echo ""
  if [ -n "$SPEC_TITLE" ]; then
    echo "Refs: $SPEC_ID — $SPEC_TITLE"
  else
    echo "Refs: $SPEC_ID"
  fi
} > "$COMMIT_MSG_FILE"
