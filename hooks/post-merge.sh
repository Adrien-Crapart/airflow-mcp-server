#!/usr/bin/env bash
# hooks/post-merge.sh
#
# After a merge, scans specs/active/ for spec files whose frontmatter
# contains "status: done" and moves them to specs/done/.
#
# Triggers automatically after: git merge, git pull
#
# Install: just hooks

set -euo pipefail

ACTIVE_DIR="specs/active"
DONE_DIR="specs/done"

if [ ! -d "$ACTIVE_DIR" ]; then
  exit 0
fi

MOVED=0

for SPEC_FILE in "$ACTIVE_DIR"/SPEC-*.md; do
  [ -f "$SPEC_FILE" ] || continue

  # Read status from YAML frontmatter (between first pair of ---)
  STATUS=$(awk '/^---$/{found++; next} found==1 && /^status:/{print $2; exit}' "$SPEC_FILE" | tr -d '"' || echo "")

  if [ "$STATUS" = "done" ]; then
    BASENAME=$(basename "$SPEC_FILE")
    DEST="$DONE_DIR/$BASENAME"

    if git rev-parse --git-dir > /dev/null 2>&1; then
      git mv "$SPEC_FILE" "$DEST"
    else
      mv "$SPEC_FILE" "$DEST"
    fi

    echo "  post-merge: moved completed spec → $DEST"
    MOVED=$((MOVED + 1))
  fi
done

if [ "$MOVED" -gt 0 ]; then
  echo ""
  echo "  post-merge: $MOVED spec(s) moved to $DONE_DIR."
  echo "  Stage and commit the moves: git add specs/ && git commit -m 'chore(specs): archive completed specs'"
  echo ""
fi

exit 0
