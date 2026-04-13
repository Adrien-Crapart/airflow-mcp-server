#!/usr/bin/env bash
# hooks/commit-msg.sh
#
# Validates that the commit message follows the Conventional Commits format:
#   <type>(<scope>): <subject>
#
# Also warns when a SPEC-XXX branch has no Refs line in the message.
#
# Install: just hooks

set -euo pipefail

COMMIT_MSG_FILE="$1"
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Strip comment lines before validating
EFFECTIVE_MSG=$(echo "$COMMIT_MSG" | grep -v '^#' | sed '/^$/d' | head -1)

CONVENTIONAL_PATTERN='^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([a-z0-9_/-]+\))?: .{1,72}$'

if ! echo "$EFFECTIVE_MSG" | grep -qE "$CONVENTIONAL_PATTERN"; then
  echo ""
  echo "  commit-msg: invalid commit message format."
  echo ""
  echo "  Expected:  <type>(<scope>): <subject>  (max 72 chars)"
  echo "  Received:  $EFFECTIVE_MSG"
  echo ""
  echo "  Valid types: feat fix docs style refactor test chore perf ci build revert"
  echo "  Example:   feat(handlers): add airflow_variable_get tool"
  echo ""
  exit 1
fi

# Warn (non-blocking) if on a SPEC branch with no Refs line
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "")
SPEC_ID=$(echo "$BRANCH" | grep -oE 'SPEC-[0-9]+' | head -1 || echo "")

if [ -n "$SPEC_ID" ] && ! echo "$COMMIT_MSG" | grep -qF "$SPEC_ID"; then
  echo ""
  echo "  commit-msg: WARNING — branch references $SPEC_ID but commit message has no Refs line."
  echo "  Run 'just hooks' if prepare-commit-msg was not installed."
  echo ""
fi

exit 0
