#!/usr/bin/env bash
# hooks/install.sh
#
# Installs project git hooks from hooks/ into .git/hooks/.
# Existing hooks are backed up as <hook>.bak before being replaced.
#
# Usage: bash hooks/install.sh
#        or: just hooks

set -euo pipefail

GIT_HOOKS_DIR=$(git rev-parse --git-dir)/hooks
SOURCE_DIR="hooks"

HOOKS=(commit-msg post-merge prepare-commit-msg pre-push)

echo ""
echo "Installing git hooks from $SOURCE_DIR/ → $GIT_HOOKS_DIR/"
echo ""

for HOOK in "${HOOKS[@]}"; do
  SRC="$SOURCE_DIR/$HOOK.sh"
  DST="$GIT_HOOKS_DIR/$HOOK"

  if [ ! -f "$SRC" ]; then
    echo "  SKIP  $HOOK.sh (not found)"
    continue
  fi

  # Backup existing hook
  if [ -f "$DST" ]; then
    cp "$DST" "$DST.bak"
    echo "  BAK   $DST.bak"
  fi

  cp "$SRC" "$DST"
  chmod +x "$DST"
  echo "  OK    $HOOK"
done

echo ""
echo "Done. Hooks installed in $GIT_HOOKS_DIR/"
echo ""
