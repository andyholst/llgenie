# Board-wide census: how much of the board has no verdict at all

One PR at a time answers "is this change right". A census answers the question a reviewer is
actually asked during a churn storm: **how much of the board is unreviewable, and why**. It is the
difference between "CI is flaky today" and "21 of 31 open PRs have a cancelled run at their current
head, so two thirds of the board cannot produce a verdict" — the second is citable, the first is a mood.

## Recipe

```bash
R=asimov-agent/llgenie
date -u '+now: %Y-%m-%dT%H:%M:%SZ'                      # the clock, in the same run as the numbers
gh pr list --repo $R --state open --limit 100 --json number,headRefOid \
  --jq '.[]|"\(.number) \(.headRefOid)"' > /tmp/prs.txt
```

Then, per PR, the **latest run at the head** — never the checks rollup, which mixes jobs from
different runs and hides which run the author is actually waiting on:

```bash
while read -r n sha; do
  printf '#%s ' "$n"
  gh api "repos/$R/actions/runs?head_sha=$sha&per_page=5" \
    --jq '[.workflow_runs[]|{name:(.name|split(" — ")[0]),status,conclusion}]|@json'
done < /tmp/prs.txt
```

Bucket the answer into exactly four states, because they mean different things:

| bucket | meaning | what you do |
|---|---|---|
| `success` | a completed matrix at the head | readable; a verdict may cite it |
| `in_progress` / `queued` / `pending` | no conclusion **yet** | say "no verdict exists yet — run `<id>` is queued"; never estimate |
| `cancelled` | **no verdict** — not red, not green | needs a fresh run at a frozen head, not a fix |
| `total_count: 0` | the head was never gated at all | usually a non-`main` base; comment + `do-not-merge` |

Two more numbers turn a symptom into a cause:

- **height of the dying runs**: for each cancelled run, `jobs[].conclusion` shows whether the deciding
  job (`linux / unit`) died at 8 minutes or at 20 — the second proves the runner was working and the
  push was the killer.
- **queue shape**: `unstarted=U` from `pr_watch.py`. `U > 0` with an old head is a scheduling story;
  `U == 0` with everything queued is a real backlog being handed out. Only the three-condition test
  (unchanged head, every `duration_ms: 0`, a measured 30 minutes) justifies an infrastructure claim.

## Reporting it

- Clock and count in the same sentence — `31 open PRs · 21 with a cancelled run at their current head ·
  10 with a live one` — and name the PR numbers, because a count without ids cannot be re-checked.
- State the mechanism you verified, not a hypothesis: `concurrency: group: CI-${{ github.ref }}` with
  `cancel-in-progress: true` keys on the **branch**, so every push to a PR head kills the run in flight
  for that ref. The remediations (freeze discipline / group by head sha / `cancel-in-progress: false`
  on `pull_request`) trade runner minutes for verdict latency: price them, let the owner choose.
- File it as an issue with acceptance criteria rather than repeating it in chat — a board-wide finding
  that lives only in a DM dies with the session, and the next reviewer re-measures the same thing.

## Pitfalls

- **`gh pr checks` is not a per-run view.** A cancelled run leaves its jobs' conclusions interleaved
  with an older run's; go through `actions/runs?head_sha=` and read `conclusion` at the run level.
- **A short sha silently returns nothing** from `runs?head_sha=` — it looks exactly like "never gated".
  Pass the full 40-character sha (`gh pr view <n> --json headRefOid --jq .headRefOid`), not the
  8-character form printed for a human.
- **A draft PR can still be red.** Draft status prevents merging, not the need to record a failing gate:
  place the hold with its reason and note that the draft is why it cannot land regardless.

## Delegation census: sorting the board into what each PR actually needs

When the ask is "which ones are red or conflicting, so the dispatcher can assign them", one call is
enough — the rollup plus `autoMergeRequest`, classified into the bucket that names the required action:

```bash
R=asimov-agent/llgenie; date -u '+now: %Y-%m-%dT%H:%M:%SZ'
gh pr list --repo $R --state open --limit 100 \
  --json number,title,headRefOid,mergeStateStatus,isDraft,labels,autoMergeRequest,statusCheckRollup \
  > /tmp/board.json
```

```python
d = json.load(open('/tmp/board.json'))
for p in d:
    roll = p['statusCheckRollup'] or []
    fails = [c['name'] for c in roll if (c.get('conclusion') or '').upper() in ('FAILURE','TIMED_OUT','ACTION_REQUIRED')]
    canc  = [c for c in roll if (c.get('conclusion') or '').upper() == 'CANCELLED']
    pend  = [c for c in roll if (c.get('status') or '').upper() in ('QUEUED','IN_PROGRESS','PENDING')]
    bucket = ('CONFLICT' if p['mergeStateStatus'] == 'DIRTY'
              else 'RED'   if fails
              else 'GREEN' if roll and not canc and not pend
              else 'NO VERDICT')
```

The four buckets map one-to-one onto the action to delegate, which is why the ordering matters — test
`DIRTY` **before** `fails`, since a conflicting branch's reds are not worth a lane's time yet:

| bucket | what it needs | who |
|---|---|---|
| `CONFLICT` | a rebase onto `main`; nothing else is diagnosable yet | rebase lane |
| `RED` | a fix — but first reproduce the failing modules on `origin/main`, because a shared red is not the PR's | that PR's lane |
| `NO VERDICT` | a **fresh run at a frozen head**, not a fix | dispatcher's freeze rule |
| `GREEN` | a review, then the merge path (`auto=`, review, `CLEAN`) | reviewer / owner |

Report the census as one block — the clock, the counts, then a row per PR as
`head sha · state · hold · auto · fail=N canc=N pend=N` — and send it to the dispatcher rather than acting
on it. It is also the only honest answer to "is the board red?": usually "one red `main` plus a queue".

### Pitfalls in the classification itself

- **Zero failures is not green.** A PR with `0 failed` but `CANCELLED` rows is *no verdict*, and so is one
  whose only rows are `SKIPPED` placeholders. Classify green only when the rollup is non-empty and carries
  neither cancelled nor pending rows — otherwise the census quietly promotes the exact PRs this repo spent
  the day protecting.
- **A run can read `queued` while a sibling job has already failed.** Run-level status lags job
  conclusions, so cross-check `actions/runs/<id>/jobs` before writing "no verdict" over a real red.
- **A cross-repo (fork) PR is not "unapprovable" — measure it.** The blockers here are permission and
  review, not the head's location: `gh api repos/$R/collaborators/<identity>/permission` plus the PR's
  `reviews` answer it. What a fork really costs is different — its `pull_request` runs get a read-only
  `GITHUB_TOKEN` and no secrets — so prefer a same-repo re-push only when a leg demonstrably needs a
  secret, never as a rule of thumb.
- **Duplicate trees masquerade as a stack.** Before accepting "#B lands after #A", compare file lists:
  identical skeletons plus one lane file each, against a default branch carrying none of them, means the
  first merge conflicts the rest and rebasing resolves nothing. Report one tree plus one-file follow-ups.
- **A branch cut before a fix carries the PRE-fix version of the files that fix touched.** Closing or
  rebasing siblings then becomes a revert risk: resolving a conflict by keeping "our side" restores the
  bug the fix removed, through a merge that looks mechanical. Detect it by blob identity — equal to the
  pre-fix sha and different from the default branch means *this branch would revert that fix*:
  ```bash
  for ref in origin/main <pre-fix-sha> refs/remotes/origin/pr<n>; do
    printf '%-28s %s\n' "$ref" "$(git rev-parse "$ref:tests/test_<affected>.py" 2>/dev/null || echo MISSING)"
  done
  ```
  A `MISSING` is the stronger form of the same finding (the branch predates the file entirely). Put the
  resulting table in the close/consolidation comment with the instruction that follows from it: take the
  default branch's side for those paths, and this PR's side only for its own one-file delta.

## Which reds are one base: the index-family classifier

When a sweep turns up several reds in the same module, classify before writing a single verdict:

```bash
python3 scripts/pr_watch.py --changes-index origin/main <head-sha> [<head-sha> …]
```

One line per ref — `wiki=<agent-wiki/*.md> notes=<docs/changes.d/*.md> preflight=<yes|no> base=<merge-base>`
plus a verdict of `indexed`, `SHORT by N note(s)`, `MISSING-DIR (…rebase, do not hand-add)` or `EXTRA`.
The shapes mean different things:

| verdict | what the branch is | action |
|---|---|---|
| `indexed` | counts agree with the wiki files | a red here is **real**, judge the diff |
| `SHORT by 1` | one wiki file without its note | stale base — rebase, don't edit |
| `MISSING-DIR` | predates `docs/changes.d` entirely | stale base — rebase; hand-adding duplicates on rebase |
| `EXTRA` | an index row with no wiki file | the branch **adds** something the index does not describe |

Two independent heads rendering the same assertion string is one base, not two mistakes; that is the
sentence to put in every comment of the group, with the pair of counts as the proof.

## Posting a sweep: generate, post, read back

Build one dict per PR and one template, post with `--body-file`, then read each body back:

```python
for p in prs:
    open(f"/tmp/v{p['n']}.md", "w").write(template.format(**p))
    terminal(f"cd <clone> && gh pr comment {p['n']} --repo {R} --body-file /tmp/v{p['n']}.md")
# verify: every body must contain its own sha and `auto=none`
```

The template carries the four required facts in the same order for every PR (sha judged, the command,
the run id, `auto=armed|none`), the attribution line, the remedy, and the explicit no-`do-not-merge`
sentence with its rule-13 reason. Reading back catches the blanked spans and the truncated body that a
zero exit code hides.

## The other half: what landed, and was it verified

A sweep that only counts open PRs misses the failure that matters most — commits already on the default
branch with no conclusion behind them. Measure the merged side in the same pass:

```bash
R=asimov-agent/llgenie
# 1. what landed recently, and at which head
gh pr list --repo $R --state merged --limit 10 --json number,mergedAt,headRefOid,mergeCommit \
  --jq '.[]|"#\(.number) \(.mergedAt) head=\(.headRefOid[0:8]) merge=\(.mergeCommit.oid[0:8])"'

# 2. the check-run census at the merged head (per-status counts, not a rollup)
gh api "repos/$R/commits/<head_sha>/check-runs?per_page=100" \
  --jq '{total:.total_count,by:[.check_runs[]|"\(.status)/\(.conclusion//"-")"]|group_by(.)|map({k:.[0],n:length})}'

# 3. the default branch's own CI runs — newest first, conclusions only
wid=$(gh api repos/$R/actions/workflows --jq '.workflows[]|select(.name=="CI")|.id')
gh api "repos/$R/actions/workflows/$wid/runs?branch=main&per_page=15" \
  --jq '{buckets:([.workflow_runs[].conclusion//"in_flight"]|group_by(.)|map({c:.[0],n:length})),
         newest:[.workflow_runs[]|"\(.head_sha[0:8]) \(.status)/\(.conclusion//"-")"]|.[0:4]}'
```

Read the two together. A merged head showing `N success · M in_progress · K queued` was **merged ahead
of its own matrix**; a `main` run list whose newest rows are `pending, cancelled, cancelled` says each
merged commit's verification was killed by the next merge. Neither state is visible from the PR page,
which keeps showing green-ish counts forever.

Report it as a **post-merge record** on the PR (merged time, head sha, the census) and, if it repeats, as
an issue: state the measured gate (`branches/main/protection` → 404, ruleset rules without
`required_status_checks`) and price the options — required checks, merge queue, an auto-merge-only path,
or record-without-blocking. Note that required checks **alone** do not fix it while concurrency is keyed
on the branch: the merge then waits for *a* run that is not *its* run, which is why the two decisions
belong together.
