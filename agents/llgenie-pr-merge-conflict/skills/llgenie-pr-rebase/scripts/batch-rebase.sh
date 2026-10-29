#!/usr/bin/env bash
# One batch, one cause: rebase each branch onto the freshly fetched main, regenerate the index from
# fragments, verify notes==rows, run the two modules that were red, and push with a lease.
# Never edits a row into a diff — `make changes-index` is the only writer of CHANGES.md.
set -u
P=/home/asimov/repository/git/llgenie
cd "$P" || exit 1
MAIN=$(git rev-parse origin/main)

for spec in "$@"; do
  N=${spec%%:*}; REST=${spec#*:}; REMOTE=${REST%%:*}; BR=${REST#*:}
  WT="$P/../llgenie-wt/b$N"
  echo "=== #$N $REMOTE/$BR ==="
  git worktree remove --force "$WT" 2>/dev/null
  git worktree prune >/dev/null 2>&1
  git fetch "$REMOTE" "$BR:refs/remotes/$REMOTE/$BR" --quiet || { echo "  fetch failed"; continue; }
  BEFORE=$(git rev-parse --short "$REMOTE/$BR")
  if git merge-base --is-ancestor "$REMOTE/$BR" origin/main; then echo "  no-op (already an ancestor of main)"; continue; fi
  git worktree add -B "b$N" "$WT" "refs/remotes/$REMOTE/$BR" --force >/dev/null 2>&1 || { echo "  worktree failed"; continue; }
  cd "$WT" || continue
  if ! GIT_EDITOR=true git rebase origin/main >/tmp/rb-$N.log 2>&1; then
    echo "  REBASE CONFLICT: $(git diff --name-only --diff-filter=U | tr '\n' ' ')"
    git rebase --abort 2>/dev/null; cd "$P"; continue
  fi
  make changes-index >/dev/null 2>&1
  if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git -c user.name='Andy Holst' -c user.email='andy.holst@protonmail.com' commit -q --amend --no-edit
  fi
  NOTES=$(git ls-tree -r --name-only HEAD agent-wiki/ | grep -c '\.md$')
  ROWS=$(git show HEAD:CHANGES.md | grep -cE '^\| [0-9]{4}-[0-9]{2}-[0-9]{2} \|')
  echo "  rebased $BEFORE -> $(git rev-parse --short HEAD) · notes=$NOTES rows=$ROWS"
  if [ "$NOTES" != "$ROWS" ]; then echo "  ACCEPTANCE FAILED (notes != rows) — not pushing"; cd "$P"; continue; fi
  ROOT=$(pwd)
  if timeout 400 docker run --rm -u root -v "$ROOT":/repo:rw -v "$P":"$P":rw -w /repo llgenie/test \
      python -m pytest tests/test_changes_index.py tests/test_check_docs.py -p no:cacheprovider -q >/tmp/t-$N.log 2>&1; then
    echo "  gates: $(tail -1 /tmp/t-$N.log)"
  else
    echo "  GATES FAILED: $(grep -E '^FAILED' /tmp/t-$N.log | head -2 | tr '\n' ' ')"; cd "$P"; continue
  fi
  LEASE=$(git rev-parse "$REMOTE/$BR")
  if git push --force-with-lease="refs/heads/$BR:$LEASE" "$REMOTE" "HEAD:refs/heads/$BR" >/tmp/p-$N.log 2>&1; then
    echo "  pushed $(git rev-parse --short HEAD) (was $BEFORE) to $REMOTE"
  else
    echo "  PUSH REFUSED: $(tail -1 /tmp/p-$N.log)"
  fi
  cd "$P"
done
