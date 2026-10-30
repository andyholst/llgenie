---
name: llgenie-pr-review
description: "Use when reviewing llgenie PRs: evidence, gates, verdicts."
version: 1.26.0
author: LLGenie PR Reviewer
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [github, llgenie, pull-requests, code-review, ci, gates]
    category: software-development
    related_skills: [github, containerized-repo-verification, worktree-branch-hygiene]
---

# Reviewing PRs on asimov-agent/llgenie

<!-- host-bot-tools:begin -->

## Tools

This lane's chat session is pinned to these Hermes toolsets and no others: `clarify`, `file`, `memory`, `session_search`, `skills`, `terminal`, `todo`.

Skills that stay enabled: `github`, `llgenie-pr-review`.
Every other installed skill is listed in `skills.disabled`.
The pin is `tests/fixtures/host-bot-capabilities.json` in asimov-agent/llgenie (issue #1038).
<!-- host-bot-tools:end -->

## Local verification depth

`references/local-verification.md` — the repo's own test venv and the `-s`/`-x` trap, golden/fixture
freshness (a golden can be in the PR diff *and* stale), measuring on the data path the test actually
uses, the control shape, and the clean-HOME split for profile gates. Read it before publishing a
local red **or** a local green as evidence.

## Dispatch protocol (fleet under the planner)

When the fleet is paused the reviewer does not choose its own work; `llgenie-planner` dispatches.
Every reply opens with a status line — a report without an id and a branch is not a report:

```
BOT llgenie-pr-reviever · working on #<id> · branch <ref> · since <hh:mmZ> · blocked on <x|none> · next <y>
BOT llgenie-pr-reviever · no PR · idle · blocked on: none — no review requested yet · next: nothing until I dispatch
```

State limits in plain terms — never shorthand the reader must decode. When work is interrupted by the
per-turn tool-call cap, say it as *"I was cut off by the per-turn tool-call limit and resumed when a
new turn gave me calls again"*, not *"when the budget allows"* — in this setting "budget" reads as
money or resource, and the user has to ask what it means. Name the actual constraint (a turn's call
count) and the actual trigger (a fresh turn), never a metaphor.

A dispatch must name the PR **and the head sha to judge** (branches move under you), and the rule
is that a verdict cites the run id at that head. Verdicts are **comment-only by default**; a
`do-not-merge` is allowed only with a one-line reason *and* a one-line unblock condition in the same
comment, and lifting it is the planner's call. If the run at the head has no conclusion yet, say
"no verdict exists yet — run `<id>` is queued" and stop; never manufacture a verdict and never move
a head to produce a fresh run.

## Standing rules for this repo (they override generic review habits)

- **Never approve, never merge, never push to `main`.** No squash, no auto-merge, no
  `gh pr merge`. The merge decision is the owner's. An approval also feeds the repo's
  `auto-merge` gate, so approving is a merge action in disguise.
- **`do-not-merge` is the only thing between a green run and an automatic merge.** Any
  hold you place must survive: re-check `labels` on every pass, because peer agents
  (`llgenie-documentation-maintainer`, `llgenie-ci-pipelines-maintainer`, the fix bots) run
  under the owner's own `gh` token and can remove it or submit an `APPROVED` review that
  reads on GitHub as the owner's. Treat a foreign approval that appears while your hold is
  set as an incident, not as a review update.
- **Undo an agent-submitted approval, don't argue with it** — but first check whether the
  owner granted that agent the authority for this shape of PR (see the narrow grant below);
  if it did, the approval is legitimate and re-holding is the incident. Otherwise re-apply the label
  (`gh pr edit <n> --add-label do-not-merge`), then dismiss the review by id:
  ```bash
  gh api repos/<o>/<r>/pulls/<n>/reviews --jq '.[]|{id,user:.user.login,state}'
  gh api -X PUT repos/<o>/<r>/pulls/<n>/reviews/<review_id>/dismissals \
    -f message="Dismissed by the PR reviewer: approved by an agent under the owner's token while a hold was in place."
  ```
  `PUT` is the endpoint — the `POST` variant answers 404. Message the offending agent
  (`llgenie-documentation-maintainer`, `llgenie-issse-implementer`, …) telling it not to
  approve, not to remove another author's label, and to ask the owner instead.
- **One agent has a real, owner-granted merge authority — respect it.** The owner granted
  `llgenie-documentation-maintainer` a **narrow** grant: a **documentation-only** PR, **rebased
  with no conflicts**, **no open reviewer finding**, **green CI** → that agent may remove the
  `do-not-merge` hold and merge it. So a docs PR's vanished hold or `APPROVED` review is not
  automatically an incident: check the four conditions first. Outside that shape (an open
  finding, a non-docs diff, a conflict, a red run) the hold stands and the maintainer comments
  "ready to land, merge is the owner's". Do not re-place a hold the owner has authorised that
  agent to clear; when in doubt ask the owner, who decides per case.
  **Once the owner has arbitrated a specific PR in writing, the hold stays theirs**: if a new
  finding appears before the run goes green, *comment* it with the evidence and the exact fix
  instead of re-holding, and require the merge to be pinned to the reviewed head sha
  (`headRefOid` re-read immediately before the squash) plus a verified `closes #NNN` — a green
  run on a head that has since moved does not authorise the merge.
- **Never state an elapsed duration you have not computed.** `created_at`/`updated_at` are not
  "now": a run that has been terminal for an hour still displays a stale `updated_at`, and reading
  one as the present tense manufactured a "~90 minutes queued" claim that would have escalated a
  billing problem that did not exist (the run had lived 11m25s and was already `completed/cancelled`).
  Print the clock and do the subtraction in the same call — `date -u` plus
  `python3 -c "from datetime import …; print(b - a)"` — and only then say "queued for N minutes".
  A duration claim is an assertion about two timestamps, so cite both.
- **Do not escalate infrastructure without a duration that survives the arithmetic.** Registered-but-
  never-started jobs (`job_runs[].duration_ms == 0` on every row while small workflows complete) is a
  real platform signal, and it is the only way to tell "registered but never picked up" from "picked
  up and slow" — but it argues "no runner granted" only when **all three** hold at once:
  (1) the head sha has not changed, (2) **every** job row shows `duration_ms: 0`, and (3) that state
  has survived a **measured** 30 minutes. Any one condition alone produces a false alarm — a stalled
  queue, a moved head and a slow job all look identical from a single reading.
- **A branch that keeps moving kills its own CI, and `main` does it to itself.** `ci.yml` carries
  `concurrency: group: CI-${{ github.ref }}` with `cancel-in-progress: true`, and `github.ref` is the
  **branch**, not the sha — so every push (to a PR head or to `main` after a merge) cancels the run in
  flight for that ref. Two consequences to report, never to absorb: a PR can go a whole evening with
  no verdict because each fix pushes the verdict further away (remedy: a **frozen head**, not a rerun),
  and `main` can carry commits whose verification was cancelled by their own successors, so a red
  `main` persists with nothing on the board saying so. Report `main` as "no completed verdict at the
  head", never as green. Name the mechanism in the verdict so nobody re-runs into the same wall.
- **A PR whose base is not `main` has never been gated — it cannot be approved.** Workflows
  trigger on `pull_request: branches: [main]`, so a PR opened against a scratch/CI branch gets
  `total_count: 0` runs: no CI, no scope, no docs, only the author's description as evidence. Verify
  with `gh api repos/$R/actions/runs?head_sha=<sha> --jq .total_count` before reading anything else.
  Such a PR gets a **comment naming the base and the zero run count, plus `do-not-merge`**, and the
  substance it carries is folded into the PR that targets `main` — closing it is the owner's call.
  The failure mode this prevents is a `+39/−0` test change looking mergeable on a green-looking,
  entirely unrun branch (#853 against `ci/824-scope-wiring`, `DIRTY`, 0 runs ever).
- **Never approve on description.** A PR's body is a claim; the review is the commands. When no run
  exists at the head, say "no gate has ever run here" and stop rather than reasoning about the diff.
- **A draft is unreviewable — say so, don't count it as pending review.** Workflows, the merge queue
  and every reviewer scanning the board all skip drafts, so a draft inside the review queue is work no
  gate can see. Report it as unreviewable and name it (`gh pr ready <n>` flips it, or ask its lane);
  never fold it into a pending count, and never open one yourself.
- **Arming auto-merge is the lane's job; a green PR with `autoMergeRequest: null` is a defect you name.**
  The fleet convention is `gh pr merge <n> --squash --auto` straight after `gh pr create`, so an unarmed
  PR is not "waiting for a human" — it is a merge path nobody opened. Put `auto=armed|none` in the same
  verdict line as the counts, and treat only these as deliberate: draft, `do-not-merge`, a non-`main`
  base, or `DIRTY`. **Arming is neither approving nor a verdict** — the gate still requires `CLEAN`, so
  an armed PR whose deciding leg is in flight is exactly as unmergeable as an unarmed one, and "armed"
  must never be reported as "will merge". Read it (`gh pr list --json number,autoMergeRequest`), never
  infer it from `mergeStateStatus`. Conversely, a red PR that is armed is not a hazard either: the
  arming is inert until a green matrix exists.
- **Nothing on this repo enforces "green before merge" — check what actually gates a merge before you
  rely on it.** `branches/main/protection` answers 404 and the active ruleset carries only `deletion`
  and `non_fast_forward` (no `required_status_checks`), so a PR can be merged with its matrix still
  running and nothing records the decision. Verify with:
  ```bash
  gh api repos/$R/branches/main/protection            # 404 ⇒ no classic protection
  gh api repos/$R/rulesets | jq '.[]|{id,name,enforcement}'
  gh api repos/$R/rulesets/<id> --jq '[.rules[].type]'   # look for required_status_checks
  ```
  When a PR is merged ahead of a conclusion, post a **post-merge record** on it rather than a
  complaint: merged time, head sha, and the check-run census at that sha
  (`gh api repos/$R/commits/<sha>/check-runs --jq '{total:.total_count,by:[.check_runs[]|"\(.status)/\(.conclusion//"-")"]}'`),
  because a merged sha whose required legs never concluded is later indistinguishable from one that
  passed. Report it as a fact about the repository; the authority to merge early is the owner's.
- **Before declaring a behaviour "unpinned", grep every test module — not the one whose name matches
  the topic.** `tests/test_ci_scope_trigger.py` holds repository-wide `paths`/`paths-ignore`
  invariants and greps 0 for `merge_group`/`workflow_dispatch`/`base_ref`, while the pin for exactly
  those lives beside the classifier in `tests/test_ci_scope.py:433-443`
  (`test_the_reporting_check_survives_the_events_that_carry_no_pr`). Reporting absence in the file
  you happened to open is the reviewer's version of a false red: it accuses a PR of a gap it does not
  have, and it is the error direction that flatters the reviewer. Search the package
  (`grep -rn '<symbol>' tests/`), then read the enclosing `def test_` to name the pin correctly.
- **A string assertion on rendered workflow YAML pins spelling, not behaviour.** `assert
  "${EVENT_BASE_REF:-main}" in body` reds a correct rewrite (`${{ github.base_ref || 'main' }}`,
  a helper in `scripts/`) whose subject never changed. Flag it as a **test-quality note with an
  issue**, never as a PR blocker: the behaviour is right today and the defect belongs to whoever
  rewrites the step.
- **Judge a run's duration against the fleet's own distribution, never against one fast sample.** The
  same suite on the same runner type measured **14m, 17m and 100m** in one evening for the same ~14.5k
  tests — a 7× spread — so a 78-minute `linux / unit` is inside the observed range and calling it "hung"
  is a claim the data does not support. Report a long job as "still running since `<started_at>`, no
  conclusion" and name the range you compared against. Two consequences for anything with a clock in it:
  a proposed `timeout-minutes` / hang ceiling must sit **above the observed maximum** (60 minutes would
  have killed a legitimate 100-minute run), and a fixed wait (`ci-wait-engine-images`' 30 minutes)
  reports a slow producer as "never published" — a false negative that reads like a real 404.
- **Static verification is not a CI verdict, and a cancelled run is not a pass however green it looked.**
  A run can have 19 green jobs and the deciding job killed at 20 minutes; the correct report is "no
  verdict exists at this branch — every row below is a *static* verification at `<sha>`" (exit codes you
  ran, tests you executed, blobs you read), never "19 jobs green". Say the two things in the same
  sentence so nobody reads the greens as a pass: `linux / unit` carries the suite *and*
  `check_pr_authors`, so its conclusion is the verdict and nothing else is.
- **While a run is in progress its step logs are unreadable — quote the observation, not a guessed cause.**
  `gh run view <id> --log-failed` answers "run is still in progress; logs will be available when it is
  complete", and `gh api repos/$R/actions/jobs/<job_id>/logs` comes back empty. What *is* readable is the
  annotation, which gives the failing step name and its exit code:
  ```bash
  cr=$(gh api "repos/$R/commits/<sha>/check-runs?per_page=100" --jq '.check_runs[]|select(.name=="linux / unit")|.id')
  gh api "repos/$R/actions/jobs/$cr" --jq '{conclusion,steps:[.steps[]|select(.conclusion=="failure")|.name]}'
  gh api "repos/$R/check-runs/$cr/annotations" --jq '.[]|{message,path}'
  ```
  Hold on that — "<job> failed at `<sha>` in run `<id>`, step `<name>`, exit code `<n>`; cause not readable
  while the run is in progress" — and make the unblock "a completed run at a fixed head with that job green,
  or the failing test named and shown to red on `origin/main` too". Never invent a cause to make the hold
  read stronger.
- **CI job logs ARE readable mid-run — `gh run view --log-failed` lies about that.** `gh run view
  --log-failed` refuses while the **run** is in flight even when the **job** has completed, and the
  bare `gh api …/jobs/<id>/logs` returns 0 bytes because of a `gh` guard, not an API limit. Use:
  ```bash
  gh api repos/$R/actions/jobs/<job-id>/logs --allow-escape-sequences \
    | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'FAILED|Error [0-9]'
  ```
  That produces the exact `FAILED tests/...` lines while the **run** is still in flight, matching a local
  reproduction on `origin/main` test-for-test. **A job that is still running is the one exception**: its
  blob can answer `BlobNotFound` (404) with nothing to grep, which means *no output flushed yet*, not
  "logs are unavailable" — so fall back to the annotation (step name + exit code) plus the job's
  `started_at`/duration, and say which of the two you are quoting. Never report "the cause is unreadable"
  without trying the recipe first, and never report the 404 as a broken tool.
- **Verify the merge took your sha, not that your commit exists.** A fix can be stranded on the branch
  and the PR merged at the head before it: `#767` merged at `24576633` while the census fix `babba17`
  sat one commit further on, so `main` kept the stale numbers and every report still read "fixed".
  Before pushing evidence into a PR, confirm the PR's head is the commit you built; after a merge,
  `git merge-base --is-ancestor <your-sha> origin/main` → must be true.
- **A baseline is a sha, and a verdict is bookended** (rule 15, #873). Two halves for this lane:
  (1) **every "passes on `origin/main`" claim names the `main` sha it was measured at** — fetch
  immediately before the worktree, `git rev-parse --short origin/main`, and write it into the comment
  ("`origin/main @ 5017128e` · same two modules → 21 passed"). Without the sha, "main passes" is a claim
  about a tree that may have moved under the verdict, and `main` moved 12+ times in one night here.
  A number about your own artifacts is the same kind of claim when someone else quotes it** — a line
  count, a test count, a "three rules once each" in a dispatcher's message describes the file as they
  last measured it; re-run `wc -l` and the test file before you repeat it, and correct the number on the
  PR or in the reply rather than letting a stale figure become the board's fact.
  **The concrete form (#1015): fetch main into a ref that cannot be the shadow, and cross-check the API.**
  `git fetch origin refs/heads/main:refs/remotes/live/main`, then read `refs/remotes/live/main` and
  require `gh api repos/asimov-agent/llgenie/commits/main --jq .sha` to equal it — `origin/main` (and a
  planner-quoted sha) can lag the true tip, and on a fast board both often do. A planner's "main =
  `6b8fafcf`" was already stale the minute it arrived; the explicit refspec + API read cannot lie about
  which tree you measured. Match first, then say "baseline = <sha>".
  (2) **bookend the work**: a start comment (PR id, the `main` sha, what "done" means) and a finish
  comment (head sha, what changed, the run id or command that proves it, what is still open). A finish
  with no start has no baseline; a start with no finish is an abandoned claim. Both lines go to the
  dispatcher too, so no lane acts on a premise another lane already invalidated.
- **Post the verdict where the work lives — sha, command, run id, on the PR** (rule 14, #873). A
  verdict that exists only in a DM does not exist for the lane that will push next: the PR comment is
  the record, the DM is a courtesy copy. Every verdict therefore carries **the sha judged, the command
  that produced the number, and the run id** — e.g. "at `729027b0`, `gh api …/jobs/<id>/logs` → 4
  failed, and `origin/main@5017128e` passes the same modules". And when the branch you are judging is
  one another lane is actively pushing, **message that lane with the head sha** before or as you post,
  because a verdict on a head that has moved is a fact about the past. Silence between two lanes on
  one set of files is how a green gets discarded twice. A DM can also fail to arrive at all
  (`queue_full`, "do not resend") — that is never a reason to retry it or to hold the finding in chat:
  put the actionable half on the PR/issue first, then treat the DM as the courtesy copy it already is.
- **Never hold a PR without a remedy** (rule 13, #873/#948, owner instruction). `do-not-merge` means
  "there is a concrete defect with a tracked fix", never "this lane would rather not": never place it
  unless the PR is **totally wrong or conflicting**, and if you do, **file the issue that makes the tag
  removable**, name its number in the comment with the exact removal condition, and **remove the tag
  yourself** when that issue lands, naming the sha or run id that proves it. A bot-implemented PR can
  never carry the tag by default; "I am not confident" is a review, not a label. Applied at this desk:
  #786 (no verdict ≠ defect), #788 and #846 (reason expired), #904 (kept — it names #949).
- **Two tools, never confused — and the test is one sentence.** *Request changes / a verdict comment*
  means **"this PR is not right yet"**: no label, no issue, and it expires with the next review.
  *`do-not-merge`* means **"there is a concrete defect with a tracked remedy"**: it needs an issue
  number, the exact condition for removal, and **you** removing the tag when that issue lands (naming
  the sha or run id that proves it). The checkable form: **if you cannot name the issue that fixes it,
  you are reviewing, not holding.** `mergeStateStatus` reads `BLOCKED` either way, so an expired hold
  and an abandoned PR look identical on the board — which is why the issue number is the whole point.
- **A `do-not-merge` must name the issue that removes it** (owner rule, #948): a hold is for *totally
  wrong or conflicting*, never for "unverified" — `cancelled`/`queued` are no verdict. When the resolving
  issue lands, **remove the tag yourself** rather than waiting to be asked.
- **A verdict ends in an arm state** (owner directive, #873/#948). Every verdict line carries four facts,
  not three: the sha judged, the command, the run id, and **`auto=armed|none`** — plus the reason when
  none (draft, hold, `DIRTY`, non-`main` base). A verdict that leaves a green PR unarmed is a verdict the
  merger cannot act on, so the state is reported on every PR, not just approved ones. **This lane records
  the arm state; it does not set it.** `SOUL.md:34` and `agents/manifest.json:["never-merge"]` forbid this
  lane from running `gh pr merge`/`--auto`, so if the arm state is `none` on a PR that is otherwise
  mergeable, the remedy is a one-line hand-off to the dispatcher ("green at `<sha>`, run `<id>`, `CLEAN`,
  unarmed — arming is yours"), never a silent arm from the reviewer. When a directive asks this lane to
  arm, the contradiction with `never-merge` is **escalated on the PR with both line numbers**, not
  resolved by whichever instruction was read last. Companion rules that travel with it: `do-not-merge`
  only for genuinely wrong/conflicting work, and the comment must name the issue that resolves it;
  **a merged PR must never carry a hold** — remove the tag and say why in one line; comment on the issue
  *and* the PR at start and at finish.
- **A hold points at a sha, not at a PR.** When the head moves, the hold's reason describes history:
  restate it against the current sha with a fresh one-line reason and one-line unblock, or it silently
  becomes a hold whose stated reason no command can reproduce (#846 moved `62ec40d8 → 7384267f` while
  held). The same applies to every verdict already posted.
- **"Stacked PRs" may be parallel copies of one unmerged tree.** Before accepting a cascade plan
  ("#B rebases after #A lands"), list the files of every PR in the family:
  `gh pr view <n> --json files --jq '[.files[].path]'` for each, and `git ls-tree -r origin/main --name-only | grep -c '^<dir>/'`.
  Five `agents/` PRs each carried the identical 16-file skeleton plus one lane file, against a `main`
  with zero files under `agents/` — so the first to land turns the others into conflicts in every shared
  file, and a rebase then "re-adds" existing files, where resolving by taking either side silently drops
  a lane's entry. The honest report is "one tree + N one-file follow-ups", not an ordering.
- **A lane with no SOUL PR is a hole in any "all lanes" change.** See
  `references/agent-profile-tree-review.md` for the gate commands, the `CHECK=1` byte-identity rule,
  the `live-longer` finding that blocks a tree from landing, **the one-directional blind spot (a
  live-only file is invisible to the gate — never read "0 absent-file findings" as "everything is
  versioned")**, and the versioned-copy staleness cadence (`CHECK=1` exit 2 = the TREE is short;
  sync at PR-open, not continuously). **Recording a lesson in the live skill IS what makes a held
  versioned copy stale**: every review pass that updates the live lane skill breaks the branch's
  byte-identity within minutes, so a held PR either opens first and takes later lessons as follow-up
  PRs, or costs one re-sync per lesson (five in one evening is the measured rate). Neither is wrong;
  what is wrong is reporting the copy "in sync" without re-running `cmp -s` after the last edit.
  When a tree change claims to carry
  every lane, count the lanes against the PRs: five of six had one, the reviewer did not, and its own
  `SOUL.md` write was refused by the harness as a protected file. Put the complete file in a PR comment
  (`ready to commit`, verbatim, plus the `manifest.json` diff) so the omission is impossible rather than
  merely noted — and say plainly that a guard was not routed around.
- **A branch can move between your verification and your comment.** On a live board a lane pushes
  while you write, so a verdict is only ever about one sha: re-read `headRefOid` immediately before
  posting, put the sha in the comment's first line ("verdict at `<sha>`"), and if it moved, say so
  and re-review rather than letting a comment about an old tree stand as the verdict on the new one
  (it happened on #835: `f5d96798` → `52e951eb` mid-post, and the new commit reintroduced the very
  defect the old one had fixed). **An `APPROVED` review does not transfer to a newer head either**: if
  the approval or the review were submitted at a sha you did not read, say so — "reviewed at `<old>`, an
  approval now exists on `<new>`, which I have not reviewed" — re-review the delta at the new sha, and
  for a `do-not-merge` with the reason "approved on a head whose deciding leg has not concluded, and on a
  head I have not reviewed", unblock "a completed run at `<new sha>` with `linux / unit` green plus a
  review at that same sha".
- **Exit codes ARE the control, and a "safe" selection with a red exit is still a red.** A gate can
  widen to everything and *still* fail the run (#850's empty-diff case: 22 of 22 selected, `return 2`),
  which reds the always-on check on exactly the trigger shapes that legitimately have no diff
  (`workflow_dispatch`, `merge_group`). When a dispatcher's ruling and the code disagree, hold and
  anchor the unblock condition in **both** — the ruling *and* the issue's own words — plus the test
  assertion that has to change, so the fix cannot be "documented" without the pin moving.
- **A changed control is escalated, never absorbed.** When a PR under review alters the property it
  was approved for (`scope` failing *closed* → failing *wide*), the reviewer states the old and new
  behaviour with commands and hands the ruling to the dispatcher/owner. Silently accepting "the new
  behaviour is safer" converts a stated decision into a silent one, which is the exact failure the
  review exists to prevent.
- **Queue labels are the planner's board state, not the reviewer's.** `agent:implement` /
  `agent:ready` and friends dispatch a lane; stripping one because it duplicates finished work is
  the planner's call (it can see every lane's queue — that is how it caught #832-vs-#835). The
  reviewer REPORTS the contradiction with proof ("this label dispatches a lane at work already on
  the branch at `<sha>`") and leaves the label alone. Same for lifting a `do-not-merge`: the
  reviewer places it with a reason + unblock condition, the planner lifts it. Touching either is
  indistinguishable from a lane editing its own backlog.
- **Never push to a branch you were not dispatched for.** Rewriting someone else's branch — even
  a "harmless" identity amend with a byte-identical tree — moves the head and **cancels the CI run
  in flight at it** (a `--force-with-lease` on `ci/824-scope-docs-class` killed run 40720371664
  while it was 18 jobs green, and the loss was attributed to another lane for an hour). A branch
  that is wrong gets a COMMENT with the exact fix; the lane that owns it applies it.
- **A hold carries a one-line reason and a one-line unblock condition**, both in the comment that
  places it; when the unblock is satisfied the hold comes off (see the three bullets above). Check the
  tracker first: `auto-merge: disabled_manually` means the label is not a merge gate.
- **The `gh` token IS `andyholst`, so `andyholst` on the tracker may be YOU.** Labels, comments,
  reviews and approvals show that login even when a previous tick of this profile, or a prior
  session, wrote them. Never report such an action as "someone else's / not my action" and never
  assume a hold is stale on that basis: read the PR's newest comments first — a reviewer comment
  that names the defect and its fix means the hold is deliberate. (An automated tick made exactly
  this error and told the owner to lift a hold the reviewer had just placed.)
- **Behaviour changes are PRs, and a `SOUL.md` write succeeds once the file has a fresh read.** This
  lane's own instructions are versioned in the repo (`agents/<profile>/SOUL.md`), so a rule learned here
  belongs in a PR under that path. The frequent refusal is the **patch tool's stale-read guard, not a
  hard protection on the path**: a `patch`/`write_file` to a live file that has not been fully read this
  turn is refused, and a full `read_file` first makes the same write succeed. So the order is always
  BOTH `read_file` and `git fetch origin/main` before editing a lane SOUL — and when a write is still
  refused after a fresh read (approval prompt that never resolves), that is the genuinely protected
  case and it is handed over, never routed around: post the **complete file body plus the manifest
  diff** as a comment on the PR that creates the tree (`agents/` may not exist on `main` yet — check
  `git ls-tree -r origin/main --name-only | grep -c '^agents/'` first), ready to commit verbatim, and
  say plainly which guard refused the write.
- **A fleet orchestration issue (“add the symmetric hand-off block to every lane's SOUL”) is a
  versioning job, not a PR.** When the inbox routes one, the reviewer node does it in four steps with
  the measured state at each: (1) read the lane SOUL fully and check whether the block already exists
  (symmetry means the text may already be there — a re-add is a duplication, not a deliverable); (2)
  add the block to the **live** SOUL with a fresh read in front of the write, and read the result back
  for the new byte/line count; (3) check `git ls-tree -r origin/main --name-only | grep -c '^agents/'`
  — until that is non-zero there is no main-side canonical copy, and the **tree copy** in the
  agents-tree PR still needs the same block; (4) post the exact block plus any contradiction it must
  also remove (a retired bullet should be retired in the same edit — dropping a retired rule is the
  other direction of the duplicate-rule defect) verbatim on the issue for the tree lane to paste, with
  the live profile's new count so the tree owner can confirm byte-identity via `sync-agent-profile
  CHECK=1`. Before claiming, read the issue thread for an existing `bot-claim:` marker and do not
  double-claim — posting a fulfillment record is not the same as claiming the work. Content in a public comment is reviewable; content in a
  DM is not. **Supersede the old body in place, loudly.** Once you post a revised body, the first
  comment a lane finds is still the stale one: open the new comment with "`<old-id>` is superseded and
  must not be pasted", name what changed (which rules it lacked, which contradiction it kept), and
  point at the new id. Silently posting a second, better body leaves the tree pasting the first one —
  and `check_agent_profiles.py` cannot catch it, because both versions satisfy the strings it greps.
- **Reviewing a fleet-orchestration block PR is a byte-identity check under the gate's own
  normalization, and the canonical is the PR head's `standing-rules.md` — never a sibling head's.**
  An orchestration PR (#1010/#1015 block in a lane SOUL) passes when the SOUL's stated fleet block
  matches `agents/standing-rules.md` **after the gate's own `_stated_block` transform**
  (`scripts/check_agent_profiles.py:341-365`: split on the fleet heading, take the body, `.strip("\n")`
  on both sides). A raw 1-byte difference (5,843 vs 5,842) is the *trailing newline* the gate strips —
  it is NOT drift, and the sha after the strip is the verdict. The canonical is the PR's **own**
  base/head `standing-rules.md`, which may be the *expanded* block (6,401 b) while another PR's head
  (919's `004dee37`) still carries the *older* 3,101-b snapshot — so compare the SOUL against the
  PR's head file, and attribute which canonical the base carried before you call a mismatch. Clean-up:
  ```bash
  git fetch origin refs/pull/<n>/head:refs/remotes/pr/<n>
  git show refs/remotes/pr/<n>:agents/<lane>/SOUL.md          # stated block
  git show refs/remotes/pr/<n>:agents/standing-rules.md      # canonical the PR will land
  git show <base>:agents/standing-rules.md                   # the base's version (attributes the diff)
  python3 - <<'PY'  # replicate _stated_block, compare sha
  …(split on '## Standing rules (fleet', strip newlines, sha256 both, assert equal)…
  PY
  ```
  Judge the four orchestration clauses as presence (report-back→inbox, new-PR→reviewer,
  version-here+sync `CHECK=1`, one-lane-one-PR `bot-claim:`), and confirm the reviewer lane is not
  the lane whose SOUL it is. **The verdict quotes the sha after the strip** — that is what the gate
  compares — and reports `auto=none` (orchestration SOUL PRs are approved, never armed by the
  reviewer).


- **A doc-vs-code issue that says "after #X merged" must be measured against *whether #X has merged* — and the live instance may be inside the open PR itself, reverting main's already-shipped fix.** When the ask is "verify AGENTS.md still contradicts the gate," first fetch main explicitly and check whether the PR the issue references is merged (`gh api repos/$R/pulls/<n> --jq .merged`). A merged-rebase can already have rewritten the doc, making the issue stale as a *main-state* claim while the *same* contradiction lives on the still-open PR's head — and that head often **reverts** the shipped wording (`git diff live/main refs/remotes/pr/<n> -- <doc>` shows the old text re-added). Measure both trees in one pass:
  ```bash
  git fetch origin refs/heads/main:refs/remotes/live/main
  git fetch origin refs/pull/<n>/head:refs/remotes/pr/<n>
  git show live/main:scripts/check_pr_authors.py     | grep -nE 'AGENTS_MANDATE|ALIASES|ALLOWED'
  git show refs/remotes/pr/<n>:scripts/check_pr_authors.py | grep -nE 'AGENTS_MANDATE|ALIASES'
  git diff live/main refs/remotes/pr/<n> -- AGENTS.md   # is the open PR reverting the fix?
  gh api repos/$R/pulls/<n> --jq .merged                 # premise check
  ```
  Report the state on **each** tree separately: "main is correct today (issue stale); the live instance is inside #<n> (`<sha>`), which reverts main's wording" — the fix travels with the open PR (drop the revert hunk, repoint the mandate to main's already-shipped string), not as a separate main-side PR. A gate's `AGENTS_MANDATE` string is a canary: altering it flips the gate (`make check-pr-authors`), so the doc and the mandate must be repointed **together**, never one alone.

- **Report a push as a fact about the ref, never about intent — and say local-vs-remote explicitly.**
  A commit that exists in the working tree or was committed on a local branch is NOT on the remote until
  the ref proves it: after any push, verify `git ls-remote fork refs/heads/<branch>` equals the sha you
  claimed, before you report "pushed <sha>". (Measured: a change-record commit was made locally and
  reported as if live while the fork ref still read an older sha; a peer lane caught it with
  `ls-remote`, and the correction was one push + a read-back.) The API's PR object lags a fresh force in
  the other direction too, so either direction is unchecked: after the push, `ls-remote` is the fact; before
  the push, nothing you committed is a fact about any PR. In every verdict/report that names a head,
  write which artifact proved it — `ls-remote fork` (remote fact) vs `git rev-parse HEAD` (local only).
  And a local `make check-docs` (or any local gate) is never a CI run: quote a completed run at the
  head or say the run is pending, never let a local pass stand for a remote verdict in a report.

- **A gate that "fails naming the sha" must verify the DOC's sha claim, not print its own HEAD.** When
  acceptance for a census/gate PR says it fails "naming both values and the sha", check what `check()`
  actually proves: printing `git rev-parse --short HEAD` next to the verdict is NOT verifying the
  document's own `(measured at …)` pointer — a doc can state a dangling, unreachable sha
  (`git cat-file -t <sha>` = commit but `git rev-list --all | grep -c <sha>` = 0, no `show-ref` →
  dangling) and the gate still passes while the numbers agree. Two checks tell you the sha half is
  unenforced: the gate never greps the doc for its measured-at string, and the census is already stale
  against the branch the review is measured against (diff the failing tree: `git diff --stat
  <head> <current-main> -- data scripts tests …` shows exactly the gate's own not-yet-merged files
  making the "head pass" a self-reference). Verify a census at the CURRENT main, not just at the PR
  head — the gate reading "OK" at a head that includes the gate is true only because HEAD contains the
  gate.  The fix belongs in `check()`: parse the doc's `(measured at \`<sha>\`)` and fail when it
  disagrees with `git rev-parse --short HEAD`.
  **Endorse a document-stated sha invariant that is COUNT-based, not literal-from-new JOINED HEAD: the
  doc lives inside the tree it measures, so `pointer == HEAD` is unsatisfiable-by-design (writing the
  census changes HEAD, so the doc can never be "current" and every census edit re-heads itself). The
  correct failure contract is: pointer must be a real commit (`cat-file -e \`{sha}^{commit}\``) AND its
  tree must carry the same `git ls-tree -r` tracked-file count as HEAD — that catches drift when the
  tree grows past what was measured (exit 1 with "measured at X (N-file tree) but HEAD is M-file
  tree") while staying green through the squash. Accept it over a literal sha-equality check, citing
  the self-heading argument, and prove all three controls at the fixed head: positive green, dangling
  red, count-drift red.**
  **When the finding is "the PR works but a half of its stated acceptance is unwired", that half is a
  tracked remedy, not a silent note: file the issue with its acceptance criteria, link it into the
  PR verdict comment (rule 13 — a finding that is not grouped as satisfied names the issue that
  settles it), and report it with the PR to the inbox. The verdict stays "approve-with-one-fix",
  never "approve with a secret caveat".**
  **A gate wired into `ci-unit` must be classified in `scripts/issue_bot_gates.py` (FAST_GATES — the pinned
  six, never widened without #475 — or DEFERRED with a reason), and a missing classification reds the
  suite `tests/test_issue_bot_gates.py`.** When a fix adds a `ci-*` gate, check that file: a bare `make
  check-docs` add is not enough if `ci-unit` runs it. Verify the DEFERRED entry has a non-empty reason
  (`DEFERRED[gate]` guard at :204) and is not stale or double-classified. A `DEFERRED` keyed with the
  reason "re-checked on the bot's own PR where the refreshed artifact lands" is the legitimate shape —
  the census is a gates-the-bot's-PR artifact, so it is deferred, not fast.
  **Census gates measure the tree AT HEAD, so a head that moved its base re-measures differently — and
  "current main" may still be behind the PR's own base.** When a census PR rebases and the planner
  quotes a new count (e.g. 1958 → 1966), re-derive it yourself: the count must be internally consistent at
  the head (gate exit 0, doc `measured at` = a real non-dangling ancestor whose tree count MATCHES the
  head's), regardless of what current `main` counts (main may have 1960 because it lacks the PR's own ~6
  files). A `measured at` pointer is stale only when it is dangling OR its tree count disagrees with HEAD
  — the count-based invariant. And a pytest collection on this repo needs `pyyaml` installed: a
  `ModuleNotFoundError: No module named 'yaml'` in a test that imports yaml is an environment gap, not a
  code defect — install pyyaml and re-run before concluding.
  Finally, never quote a completed CI run that does not exist: if the `CI` run at the head is
  `in_progress` (holds may be `success`), say exactly that and withhold the verdict's merge-eligibility.
  A re-verdict can be `clear-to-approve-once-CI-concludes` when every local gate passes but the deciding
  leg is still running.
  **A docs-only census-refresh PR is verified exactly like the gate it refreshes: independent recounts
  plus the pointer's reachability, and a green-ci-scope is its verdict.** Four independent `git ls-tree
  -r` recounts must equal the doc's claims (tracked, openspec-changes, agent-wiki, docs, test_*.py) —
  never trust the doc's own numbers. The `measured at` pointer must be a real commit that is a REACHABLE
  ANCESTOR of the head (`git merge-base --is-ancestor <sha> refs/pull/<n>/head` = yes) with a tree count
  equal to HEAD's — a dangling or count-mismatched pointer is the self-reference gap the gate closes. A
  docs-only PR correctly triggers NO `linux / unit` run: `ci-scope` runs the docs gates a docs-only diff
  needs, so the verdict is the `ci-scope`+`holds`+`guard` runs being `completed/success` with no pending
  row — do not flag the absent unit leg as a missing run, that is designed behavior.
  **A census gate's correct referent is "the tree at the sha the DOC names", not HEAD — and the pointer
  must be an ANCESTOR of HEAD, not merely a real commit.** A file-adding PR that never touches
  `docs/ARCHITECTURE.md` must pass: its doc names a main ancestor whose tree the numbers describe, so
  `check()` runs `git ls-tree -r --name-only <pointer>` (not HEAD) and passes even when `measure(HEAD)`
  is larger. The ancestor test (`git merge-base --is-ancestor <pointer> HEAD`) is the half that a
  real-but-unreachable pointer (a branch head that dangles after squash) needs: `cat-file -e` proves
  existence but an unmerged sha is not reachable from HEAD and must red naming the sha, or it dangles
  after the next squash. When reviewing such a fix, prove all three by EXECUTING at the PR head: (a) the
  head's own tree count exceeds the pointer's (e.g. HEAD=2005 vs pointer=2002) yet `check()` exits 0 —
  the self-proof that the gate reads the pointer's tree; (b) its new contract test drives the REAL
  `check()` against a throwaway repo (assert `measure(HEAD)==measure(doc)+N` to prove files were really
  added, a non-ancestor reds NAMING the sha, a missing pointer reds naming ARCHITECTURE.md) — a test
  that only greps strings is a weakened assertion; (c) stale counts at the pointer still red. A CI run
  that is `in_progress` with only the deciding leg pending is no completed-run verdict — say so and
  make the verdict `clear-to-approve-once-<leg>-concludes`, quoting the completed `ci-scope`/`holds`
  run ids and the `CI` run id separately.
  **When a test reds, attribute which side changed before blaming the product — and if the PR rewrote
  the test, suspect the oracle first.** A local red under the suite's own interpreter (the gguf venv at
  `~/llama-gguf-tools/.venv/bin/python`, not the tools python) is a lead, not a verdict: run the same
  cases on `live/main`, then swap one side. Measured example: a PR added an `arch` parameter to
  `fits()` (which now excludes Apple/Metal runs on a non-Metal host) and rewrote the acceptance oracle
  — but the new oracle called `mp.fits(m, gb, ram)` **without** `arch`, so `arch=None` counted runs the
  product correctly drops, and 8 of 12 backends red while the product was right (`fits(arch=backend)`
  == `offer()` rows exactly). Prove the remedy, don't assert it: apply the one-token fix, run, and
  report the before/after counts (`8 failed` → `12 passed in 0.86s`), then restore the file. A
  red-then-green claim in a change record survives an actual injection of the old bug (inject → N
  failed → restore → all pass); take that measurement rather than the PR's word for it.
  **When both readings are defensible, the PUBLISHED SPEC decides — not the reviewer's instinct and
  not a dispatcher's ruling.** "The product over-admits" and "the expectation is stale" are both
  consistent with the same diff, so reading the diff cannot settle it. Find the document the product
  is obliged to satisfy — the vendored README's tier table, a contract doc, the criterion the gate
  cites — and check which side contradicts it. A subject listed FIRST in the published `Up to 8 GB`
  table being admitted at 8 GB means the assertion encoding the old refusal is stale, not that the
  gate is loose. Parse the table and quote it (tier → row count, the subject's position) so the call
  is a measurement rather than an opinion. Then name the acceptance that must survive either way: a
  rewrite justified this way can drop the invariant it was protecting, so ask for the same rule as a
  hermetic test — a semantic change must not arrive as a merely deleted assertion.
  **A published control expires with the base it was measured on — re-run the PAIR, not just the branch
  side.** "Branch fails, base passes" is a claim about two trees, so it is only valid while both shas are
  current; when `main` moves, the branch half is unchanged but the base half is history, and repeating
  the finding against a superseded base is the same staleness this skill refuses everywhere else. Re-run
  both halves against the new tip in one environment before repeating it. When the fixture does real
  work (a live fetch, a download), near-identical wall-clock on both sides — 7.3 s vs 7.5 s for a fixture
  that syncs upstream — is itself evidence: it proves neither run was cached, skipped or short-circuited,
  which is what makes "same data, same command, different code, different verdict" a measurement rather
  than an assumption. Quote both durations and both shas.
  **A test that states one expectation twice must move both sites together.** The same rule often appears
  as a direct assertion and again in a pinned/derived table in the same file; changing the product to
  satisfy one and leaving the other is a silent expectation edit that reds later on a path nobody ran.
  Grep the file for every form of the expectation (`grep -n '<subject>' <test file>`) and say in the
  finding that both sites move together, or hand the semantic call to the file's owner with both line
  numbers — never "fix the assertion" in the singular.
  **The nerve completion guard false-positives on every review-only turn in this lane — leave it,
  report it, do not satisfy it artificially.** `progress_integrity.change_required()` matches the verb
  regex `\b(fix|implement|modify|...)\b` against the delegation text, so a branch name like
  `fix/669-card-gate-vram` sets `change_required=True`; `requested_paths()` then scrapes every
  file-looking token from the SAME message — which are the files the delegation tells you to
  INSPECT (`docs/ARCHITECTURE.md`, another lane's `agents/<lane>/SOUL.md` / skill, a wiring fixture).
  `mutation_is_relevant()` needs a mutation path equal-or-suffix-related to one of those, so with
  `requested_paths` populated no legitimate mutation can ever match → permanent
  "no task-relevant mutation was attempted". Diagnose it from the guard's own log
  (`<profile>/nerve/gate-events.jsonl` → the `progress_completion_blocked` row shows
  `requested_paths` + `relevant_mutation_attempts`) and its source
  (`<profile>/plugins/nerve/hermes_nerve/progress_integrity.py`), never by guessing. **Do not** edit
  another lane's PR files to appease it: for a review lane the deliverable is the verdict comment
  (head sha + executed evidence + run ids), not a repo mutation; owner ruling is to leave the guard
  and report each block as a known false positive. A genuine, honest repo record (change note +
  fragment, `make check-docs` exit 0, pushed to your own ref) is fine as extra evidence but will still
  not clear the guard — that is expected. Read its own `nervous-events.jsonl`
  `progress_completion_blocked` row on every fire: it prints `requested_paths` (scraped from the
  delegation text) and `relevant_mutation_attempts`, which is how you refute a blanket "only PR
  comments and scratch dirs" claim with the turn's actual work. **The scrape is a bare regex**
  (`PATH_RE = [A-Za-z0-9_.-]+\.[A-Za-z0-9]{1,12}`), so it treats quoted EVIDENCE tokens as file
  paths — a planner message quoting your own proof (`Qwen3.6`, `mp.fits`, `0.86s`, branch names like
  `fix/669-card-gate-vram` as the `fix` verb) yields `requested_paths` no real file can be related
  to, and the gate is then unsatisfiable no matter what you do. That is the signature to report: if
  `requested_paths` contains anything that is not a path, say so with the log line and stop, rather
  than committing churn to appease it. **The scrape can also come from a system notification, not just
  a delegation.** A background job/DM-delivery notice carries the command that ran it, so
  `requested_paths` fills with an interpreter path, a tool's own script and a scratch query file —
  none of which is a file the task ever asked you to change. Same signature, same response: quote the
  log line, do the real work, do not touch the unrelated path. Deliver the actual artifact first (verdict comment with head
  sha + run ids; a filed issue with evidence; a gate-green record on your own ref) — the guard is a
  supervisory heuristic, not the definition of done for a review lane.
  **Grep BOTH call forms before reporting a fix absent** — a keyword-form fix (`fits(m, gb, ram, arch=x)`)
  does not match a positional grep, and an empty result is evidence the grep was wrong. More evidence
  discipline (both forms, verdict expiry, stacked-branch bases, cited-row verification, the doc as
  oracle) is in `references/evidence-and-bases.md`.
  **A pytest marker is a SELECTION, not a verdict — a mark can move a red out of `ci-unit` without
  fixing it.** When a branch answers a failing test by adding `@pytest.mark.network` (or an
  exclusion), re-run the test **under the marker's own pipeline** (`-m network`), not just the
  hermetic one: on #935 the newly-marked test still failed (`1 failed, 1 passed` under `-m network`)
  while the same test **passed on `main` with the same upstream and fixture**. The control is what
  distinguishes an in-diff defect from environment: same code on base passes ⇒ the branch differs ⇒
  it is in-diff, and "live-data" is the wrong classification. State both measurements; do not
  accept a mark as a resolution, and do not let a green `-m 'not network'` collect be read as green.
  **A same-scope static regex cannot see a live call made through a helper module** — an auditor that
  scans each test file for a primitive plus a host literal passes one whose fetch lives hundreds of lines
  away, so ask what the gate cannot: is the file in the hermetic roster (`import unit_tests as ut;
  '<file>' in ut.select('.')`, absent from `excluded`/`deselect`), and does its fixture reach out.
  `references/gate-auditing.md` carries the four audit recipes and the negative-control shape.
  **A local red in a gate that reads the LIVE profile home is not the branch — re-run with a clean
  `HOME` before calling it a defect.** `scripts/check_agent_profiles.py` compares the tree against
  `~/.hermes/profiles/<profile>/`, so on a host whose live profiles have drifted (the #1060 class) it
  reports findings that CI never sees; `HOME=/tmp/clean <venv>/bin/python -m pytest
  tests/test_agent_profiles.py` separates the two (`8 failed` on the real home → `104 passed` on a
  clean one, measured at #919 `e21e7b22`). Confirm with `HOME=/tmp/x python3
  scripts/check_agent_profiles.py check` — it prints "tree checks only, LIVE RULEBOOKS NOT COMPARED"
  when the live side is absent. Report the clean-home result as the branch's state and the real-home
  delta as host drift; never file the host's drift as a PR defect.
  **A change PR must NOT edit `CHANGES.md` — commit the `docs/changes.d/` fragment only.** Its own
  docstring is the authority (`scripts/changes_index.py:11`): "**rendered** from those fragments by
  `make changes-index`; **no change PR writes it**" (issue #934). `CHANGES.md` is a single shared file,
  so appending a row is the same line every other open PR appends and is the one file that turns
  every branch `DIRTY` on its own (measured: #919, #1049, #1050 all collided there, each costing a
  16–33 min matrix before any verdict exists). `make check-docs` passes with the fragment and
  `CHANGES.md` untouched — verified — so there is no gate reason to write it. If you already wrote
  it, **rewrite the branch** (drop the hunk) rather than adding a revert commit: a revert still
  leaves `CHANGES.md` in the cumulative diff. Issue #1063 gates this.
  **Quote the pushed ref in the SAME command as the push.** `git push` can print `Everything
  up-to-date` and exit 0 while moving nothing (the commit was on a scratch branch and the real ref
  still held the old sha). Always: move the ref (`git branch -f <ref> <sha>`), push with
  `--force-with-lease=<ref>:<old-sha>`, and echo `git ls-remote <remote> refs/heads/<ref>` next to
  `git rev-parse <ref>` in that one call. A null op that exits 0 is how a stale head survives.
  **Verify a decision's cited evidence is the row the code actually selects.** A ruling that says
  "the admitting run is X" can be wrong about X while being right that some run admits: a selector
  like `admitting_measurement` picks the *smallest* card at or below the target, so a smaller,
  RAM-hungrier run can be the deciding one and the cited larger run is merely present in the data.
  Enumerate the candidates and ask the function itself (`print(admitting_measurement(...))`, its
  `measurement_card_gb`, its `ram_floor_gb`) before writing the reason down — a fix made for the
  wrong row pins the wrong behaviour permanently. Also check the cited fields exist: a quoted
  `ran_on=8.0` is worthless if every entry carries `ran_on: None`. **Then check FIELD PRECEDENCE, not
  just row selection.** A gate may prefer a run's own named footprint over the model's declared
  contract field: a model whose record states a large `system_ram_min` can be admitted on a far smaller
  host because the admitting run's hardware string names less RAM, and the floor comes from the run.
  Print the model's field next to the run's (`ram_floor_gb`, `measurement_card_gb`) and say which one
  wins — a green that depends on the weaker field is a semantics question to name, not a pass.
  **Settling a claim by execution is for your own claims too.** Re-run a control against the *moved*
  base, not the one it was measured on: a clean merge, a passing test or a byte-compare measured at
  a superseded base proves nothing about the base it will land on.
  **When a dispatcher reports your work as missing something, check the live ref before redoing it — the
  ask may be measured against a head you have already moved past.** Repeated identical asks (the same
  "drop that hunk", the same "your branch is stale") are the signature: the dispatcher's snapshot is
  older than your last push, and re-doing the work produces churn plus two records that disagree. Verify
  with one call — `git ls-remote <remote> refs/heads/<ref>`, `git diff --name-only <base> <ref>` for the
  specific file, and `git merge-base --is-ancestor <the-sha-they-named> <ref>` — then reply with the
  measured state and a pointer to where it was already reported, rather than performing the change a
  second time. Never answer "already done" without the ref read: the same call distinguishes "they are
  stale" from "my push silently did not land", and those need opposite replies. **Prove "rewritten out"
  by ancestry, not by `git show`.** After a force-push that dropped a hunk, a peer reading an older
  snapshot keeps naming a sha that is no longer on the branch; `git merge-base --is-ancestor
  <the-sha-they-named> <ref>` returning NO is the one-call proof it is gone, and give them a recipe
  they can run themselves (`git fetch --no-tags <url> +<branch>:refs/tmp/x`, then `git diff --name-only
  <base> refs/tmp/x | grep -c '^<file>$'`) — repeated identical asks usually come from one stale local
  ref, not from repeated non-compliance.
  **Two failing check-runs are often ONE cause — read both job logs before reporting two defects.**
  `scope` can fail because its own step sequence runs `make ci-openspec`, so its red is the same
  red as `linux / openspec` (verified on #935: both ended in `[openspec-tasks] FAIL … lines [27]`).
  Attribute by step (`grep '##\[group\]Run …|##\[error\]'` on the job log), then report the single
  cause, not a count of red rows.
  **A commit on a detached HEAD is not on your branch.** `git push <remote> <branch>` after
  committing in a `--detach` worktree pushes the OLD ref and says `Everything up-to-date` while the
  new sha sits only on HEAD. Move the ref first (`git branch -f <branch> HEAD`), re-push, then
  compare `git ls-remote <remote> refs/heads/<branch>` against `git rev-parse <branch>` — and say
  explicitly that they match.

- **A merged lock still gets re-verified on every main move the monitor reports — merge is not the
  end of its job.** When a PR that a reviewer previously verified as an OWN lock test later merges and
  `main` advances (a sibling PR lands on top), re-run the assertions at the new head, executed not
  grepped: fetch the explicit ref (`git fetch origin +refs/heads/main:refs/remotes/origin/main`,
  cross-check the API), confirm the merge commit is an ancestor of the current tip
  (`git merge-base --is-ancestor <merge_sha> refs/remotes/origin/main`), then `git show <tip>:<file>`
  for each asserted string (the mandate, the doc phrase, the test file's presence) AND run the lock
  test itself at the merged tree (`pytest …::test_the_…` → 1 passed). The question is not "does the
  PR pass" but "did the sibling's merge change anything the lock asserts" — if a new merge rewrote
  the mandate to a narrower phrasing, the lock should red and the report says so (adapt), not that
  the merge is clean. Post the re-verify where the PR lives with both shas (the merge commit and the
  current tip) and say explicitly a local pass is the lock executing at that head, not a CI run.

- **A verdict wave is not complete until it changed something it owns — and an unbranched branch change
  is invisible to an integrity check.** Posting verdicts is the *output*; the *task-relative change* is a
  concrete mutation a checker can verify on a path it tracks. The reliable one this lane can always make
  and prove: keep its own contributions current on the fresh main the wave measured. If a review hands
  back a stale PR that is **this lane's own** (a fix/test it authored), rebase that branch onto the just-
  fetched `main` (per #1015, only when actually `CONFLICTING` — a stale `ms=blocked` needs no rebase, but
  an own-PR it will hand to another lane for merge should not sit on a base main has passed), verify the
  changed file is byte-identical across the rebase (`sha256sum` on the pre- and post-rebase blobs, `git
  diff <old> <new> -- <file> | wc -l` = 0 means the earlier test run still applies), re-run the author
  gate on the rebased range, then `--force-with-lease` to the fork. **After a force-push, verify via the
  ref read, never the PR object**: `refs/pull/<n>/head` and the `head.sha` in the pull API both lag a
  fresh force, so read `git ls-remote fork refs/heads/<branch>` and compare against local `HEAD` — the
  ref is the fact, the PR object is a cache.

- **A rule stated twice is two texts that drift — dedupe, never restate.** A behaviour block pasted
  into a tree twice is not "extra emphasis": the copies diverge (one punctuates the bold, one does not),
  and then two lanes disagree about what the rule says — the same family as a rule satisfied by a
  quotation. The profile gate cannot see it, because it matches regexes on the text and one occurrence
  satisfies `never\s+merge`; the duplication has to be counted. One call per ref:
  ```bash
  python3 scripts/pr_watch.py --soul-rules <ref>     # same tree as origin/main when main has no agents/
  # <ref> llgenie-<lane> r13=1 r14=2 r15=2 verdict=DUPLICATED r14,r15
  # <ref> llgenie-<lane> r13=0 r14=0 r15=0 verdict=ABSENT r13,r14,r15
  ```
  Three verdicts, not one: `ok` (stated once), `ABSENT` (a rule the lane cannot apply), `DUPLICATED`.
  The repair is to **delete the second block** in each lane, not to reconcile the two wordings; and a
  lane whose file says both "never run `gh pr merge`" and "arm auto-merge" must be escalated with both
  line numbers, because its own manifest (`never-merge`) contradicts it while the gate stays green.
  **A rewrite can drop a rule, and that is the same defect from the other side.** When you condense or
  dedupe a rule block, re-count *every* standing rule in the committed blob afterwards — a rule that
  silently vanished during the edit is indistinguishable, to the next reader, from one never written.
  Count on the blob, not the worktree: `git commit --amend --no-edit` alone commits only what is staged,
  so a file copied over the old one and then amended without `git add` keeps the previous tree and every
  re-read of the working copy agrees with the version you did not commit. `git add <path>`, amend, then
  `git show <sha>:<path> | grep -cF '<rule>'` for each rule and quote the sha you counted.
- **You cannot review your own PR.** `andyholst` authors most PRs here, and `gh pr review
  --approve/--request-changes` fails on your own PR. Use `gh pr comment` for those; reserve
  `--request-changes` for bot/other-author heads (`asimov-agent`, contributors).
- **Wrong or failing ⇒ make it unmergeable**: `do-not-merge` + a review/comment with the
  evidence. Clear the hold when the finding is fixed AND the owner is ready — the reviewer
  verifies, the owner merges.
- Every claim about CI, mergeability or diff content is a fresh `gh` read. A run's status is
  not its jobs' status.

## Fleet rules 13–16, verbatim (from #873's body at commit time — do not paraphrase when citing)

**13. Never hold a PR without a remedy.** `do-not-merge` means "there is a concrete defect with a tracked
fix", never "this lane would rather not". Never place it unless the PR is **totally wrong or conflicting
with something** — and if you do, **file the issue that will make the tag removable**, name its number in the
PR comment with the exact condition for removal, and **remove the tag yourself** when that issue lands
(naming the sha or run id that proves it). A PR a bot implemented can never carry `do-not-merge` by default;
"I am not confident" is a review, not a label. A hold whose reason expired is indistinguishable from
abandonment on the board — `mergeStateStatus` reads `BLOCKED` either way. **If you cannot name the issue that
fixes it, you are reviewing, not holding.**

**14. Announce the work where the work lives, and talk to the lane you overlap.** Before you pick anything
up, **comment on the issue or PR** saying what you are taking, on which branch, and what "done" means — a
claim is a comment a stranger can find, never a DM and never private memory. **Re-read that thread before your
first edit**: an existing claim, a live branch, or a note from the lane that touched the files last outranks
your plan. When two lanes are on the same files, or one lane's change moves the other's premise, **message
that lane directly** with the id, the sha and what you need — then **post the conclusion in the issue**,
because a decision that exists only in a DM does not exist for the next reader. Rebase, rewrite, or force-push
on a branch another lane is working is a conversation first, a command second. Silence between two lanes on
one set of files is how a green gets discarded twice.

**15. Start from a fresh upstream main, and bookend the work with two comments.** Before you create a
worktree, branch or first edit: `git fetch upstream main` (the canonical remote is `asimov-agent/llgenie`; a
fork named `origin` is not upstream) and branch from `origin/main` **at the sha you fetched in that moment** —
never from a branch you already had, and never from a sha quoted in a chat message, which is stale by the time
you read it. Write the sha you branched from into your first comment. Then **bookend**: one comment when you
start (issue/PR id, branch, the main sha, what "done" means) and one when you finish (head sha, what changed,
the run id or command that proves it, and anything left open). **Report the same two lines to the planner**,
who relays the fleet's state back to you, so a lane never acts on a premise someone else has already
invalidated. A start comment with no finish comment is an abandoned claim; a finish comment with no start
comment has no baseline to compare against.

**16. Arm auto-merge when the work is done, not when it is approved.** The last push is the trigger:
`gh pr merge <n> --squash --auto`, then **read `autoMergeRequest` back** and report the arm time in
the same comment — `gh pr merge --auto` exits 0 and arms NOTHING when the base is not the default
branch (issue #964), so the exit code is not the fact. "Done" triggers the arm, not "approved". The
one exception is a PR the owner has explicitly forbidden: report `auto=none (owner instruction)` and
say where that instruction lives.

**In this lane rule 16 means the report, not the push.** This lane owns no PRs and merges none: a
verdict reports `auto=armed|none` (with the reason when none — draft, hold, `DIRTY`, non-`main` base)
and hands a mergeable-but-unarmed PR to the lane that owns it in one line — "green at `<sha>`, run
`<id>`, `CLEAN`, unarmed — arming is yours." Running `--auto` on a branch this lane did not author
would bypass the lane that owns it, and `agents/manifest.json` declares `never-merge` for it. The
retired **"arm at PR creation"** bullet is not part of this lane: it exists for lanes that open pull
requests, and a file carrying both it and rule 16 contradicts itself (measured on #919 at `4fb3bf3a`:
`:20` "no auto-merge, no `gh pr merge`" beside `:73` "arm at PR creation").

**Companion owner rules (#948), same block:** `do-not-merge` only for genuinely wrong or conflicting work,
never as a default or a placeholder, and the tag comment must name the issue that resolves it or the tag
cannot come off. **A merged PR must never carry the tag** — remove it and say why in one line. Comment on the
issue *and* the PR where the work lives when you start and when you finish.

### Reviewing a `do-not-merge` PR against its lifting issue (#949 template)

When the ask is "check the five criteria in the lifting issue and say which line makes the tag
removable", the verdict is per-criterion, measured, and the tag is **not** touched:

- Run the two named modules at the PR head **and** on `origin/main @ <today's sha>` in the same
  breath; `5 failed, 20 passed` at the head with `25 passed` at the baseline means every red is the
  branch's, and the baseline sha makes that a measurement not a claim.
- A gate's failing **case** is the evidence, never its passing count: `test_every_dispatchable_workflow_has_the_guard`
  failing on `scope.yml` means "a dispatchable workflow carries no guard", which is the privilege
  hole (issue #295). Quoting "2 of 5 criteria fail" is weaker than naming the workflow.
- Distinguish *why* a job fails: `ci-scope` red on `[changes-index] … is not indexed` is the shared
  missing-note base (#855/#915/#940 family), not necessarily #904's classifier. Say which of the two
  it is — a doomed-to-fail-before-rebase criterion and the PR's own guard gap are different fixes.
- **Do not remove the tag** on an owner-applied `do-not-merge`; the review is what the owner lifts
  on. Name the exact acceptance line that flips it ("the tag stays until this lands", criterion 1 →
  `0 failed` at the rebased head with `scope.yml` in `_guard_steps()`).

## Loop

```bash
R=asimov-agent/llgenie
gh pr list --repo $R --state open --limit 100 --json number,title,author,headRefOid,headRefName,baseRefName,isDraft,reviewDecision,mergeStateStatus,mergeable,labels,statusCheckRollup
gh pr checks <n> --repo $R                 # triage from CHECKS, not `gh run list`
gh pr view <n> --repo $R --json files,body,commits,comments,reviews
gh pr diff <n> --repo $R > /tmp/pr<n>.diff
```

Re-read `headRefOid` on every pass: a branch can be rebased under you (the rebase bot and
the peer maintainers do it), and a verified head sha is the only thing your verdict applies
to. Verify **at the PR head in a worktree**, never from the description:

```bash
git -C /home/asimov/repository/git/llgenie fetch origin pull/<n>/head
git -C /home/asimov/repository/git/llgenie-wt/<name> status -sb   # reuse an existing tree if present
# else: git -C /home/asimov/repository/git/llgenie worktree add --detach ../llgenie-wt/pr<n> <sha>
```

`origin` in this clone is the UPSTREAM (`asimov-agent/llgenie`); the fork is `fork`
(`andyholst/llgenie`) — the opposite of the usual layout.

## What actually blocks a PR

| Signal | Meaning |
|---|---|
| `mergeStateStatus: BLOCKED` | a gate is outstanding — usually the required review or a pending check. NOT a conflict. |
| `mergeStateStatus: UNSTABLE` | checks still reporting; `auto_merge.py` needs `CLEAN`, so an unstable PR cannot land yet. |
| `mergeStateStatus: CONFLICTING` / `mergeable: DIRTY` | the merge would fail; needs a rebase. |
| `macos / unit` **pending** | a scarce macOS runner still holding the run; the PR sits `BLOCKED` while everything else is green. Say that, never "failing". |
| check conclusion `SKIPPED` / `ACTION_REQUIRED` | a form-driven placeholder (`test-published-${{ matrix… }}` is normal) or a human gate — not a test failure. |
| check conclusion `CANCELLED` | **not a failure and not a verdict**: a cancelled/superseded run cancels every sibling job, so a green PR shows a page of `cancel` rows. Report it as "needs a fresh run" (`gh run rerun <id>` at the same head), never as red — and never push an empty commit to fake a fresh run. `pr_watch.py` therefore counts `cancel=` separately from `fail=`. |

## Repo gates that a change must satisfy (pick per diff)

`ci-unit` chain in `Makefile`: `skills-validate` → `check-engine-skill-gap` →
`check-engine-params` → `check-engine-coverage` → `check-engine-source` → `check-wiring` →
`check-secret-output` → `check-docs` → … plus `openspec` (Linux **and** macOS) and
`check-pr-authors`/`check-pr-hygiene`. A new user-facing make target needs, in order:
`.PHONY`, a `DEFERRED` entry in `scripts/issue_bot_gates.py` (never `FAST_GATES` — its
membership is a contract asserted by a test), a mention in `README.md` or a linked
`docs/` page (`check-docs`), and a truthful "CI" help line (`check-wiring`). Every
`openspec/changes/<name>/tasks.md` box must be ticked in the code commit.
See `containerized-repo-verification/references/llgenie-engine-pipeline.md` for the
engine → image chain and `worktree-branch-hygiene/references/llgenie-repo-notes.md` for
the gate order and flakes that are not the author's. For keeping a verdict tied to a real base —
rebasing off a squash-merged ancestor, and re-verifying your findings on the merged sha — see
`references/base-and-merge-integrity.md`.

## Traps that cost real time

- **`docs/ARCHITECTURE.md` is generated and its census goes stale fast, and it goes stale
  *again* the moment anything merges.** The `architecture-bot` (cron `47 */6 * * *`, issue
  #449) rewrites it as one issue + one PR, and the numbers describe the commit the bot
  measured. A bot PR rebased onto newer `main` keeps the OLD numbers and lands already
  wrong — and a refresh measured against a base that merges before its own merge is wrong
  too. Always census the branch's **current** merge base (`git rev-parse origin/main`), not
  the base you measured an hour ago. Verify with the bot's own census
  (`scripts/architecture_bot.py:tracked_files` is just `git ls-files`):
  ```bash
  git ls-tree -r --name-only <head^> | wc -l
  git ls-tree -r --name-only <head^> -- scripts | wc -l
  git ls-tree -r --name-only <head^> -- tests | grep -c 'test_.*\.py$'
  ```
  A mismatch on `HEAD^` is a blocker (stale census ⇒ `do-not-merge`), and `git ls-tree`
  counts differ from `ls -d dir/*/` — use the `git` form, that is what the generator counts.
  Reviewing a census PR means recomputing **every** number it touches, not the headline one: the
  qualifiers in the same sentence (`skills/engines/` subdirectory count plus its `README.md`,
  `openspec/changes/` directory count, the `N tests/test_*.py` figures — which appear in two places)
  are claims too, and each is one `git ls-tree` away. Finish with `make check-docs` (exit 0, and quote
  its `[check-docs] ok: …` line) because that is the gate the change must pass. Say plainly which
  number you could **not** re-derive from the tree (e.g. an engine-count line that reads the registry)
  instead of letting silence imply verification.
  Fixing a census is legitimate review remediation: edit only the numbers, keep every
  non-census sentence, commit as `Asimov Agent <support@docondee.com>` (or `Andy Holst
  <andy.holst@protonmail.com>`) so `check-pr-authors` passes, push on top (no force-push),
  and re-run `make lint check-docs`.
- **`tests/conftest.py` needs the gguf venv, so run a single test module with `--noconftest`.** It
  imports `scripts.llgenie_serve` (gguf+numpy) and a plain venv dies with exit 2 and no output — the
  silent exit 2 is a missing import in the venv, not a failing test. Two things make a scratch venv
  work in a repo worktree: `--noconftest` and `python -m pip install -q pygments` (pytest imports it,
  and without it the failure looks identical to the conftest problem). Then:
  `python -m pytest --noconftest -q -p no:cacheprovider tests/test_<name>.py`; for the whole suite use
  the container path (`make test-unit`, ~12–13 min). Do not conclude "the tests do not run here" from
  one empty log — retry with the module installed and quote the real `N failed, M passed` line.
- **Prove where a red comes from before you attribute it to the PR: reproduce it on `origin/main`.**
  A board can show five red PRs that share one broken default branch, and holding each of them parks
  work for a defect it does not carry. Check `main`'s last run first, then reproduce:
  ```bash
  git -C /home/asimov/repository/git/llgenie worktree add --force --detach ../llgenie-wt/vmain origin/main
  cd ../llgenie-wt/vmain && python -m pytest --noconftest -q <the modules named in the failing job>
  ```
  Same FAILED set ⇒ the red is **not in the diff**: write "not green, for a reason outside the diff",
  name the two commits that introduced it, and place **no hold** (a hold on such a branch parks it for
  someone else's defect). The unblock is the `main` fix, not a change on the PR. Quote the local
  counts (`4 failed, 66 passed` at the PR head vs `6 failed, 187 passed` on `main`) so the attribution
  is a measurement rather than an opinion. Never fold a shared red into a per-PR verdict without it.
  When the `main` fix itself comes up for review, close the loop the same way: run the **same modules**
  at the fix's head and quote both counts (`6 failed, 187 passed` before → `0 failed, 193 passed`
  after) instead of reading a green job, because a local pass proves the change and only
  `linux / unit` proves the gate.
- **Several PRs failing the *identical* assertions is a shared base, not several authors making the
  same mistake — and `main` passing does NOT mean the diff caused it.** A branch cut before a commit
  that added both an artifact and its index/metadata row fails "missing row" assertions while `main`,
  which has both, passes: the diff looks guilty and is innocent, and the remedy is a rebase, not an
  edit (adding the row in the diff duplicates it on rebase and reds something else). The cheap
  discriminator is a two-sided count, before any verdict — run it, never eyeball it:
  ```bash
  python3 scripts/pr_watch.py --changes-index origin/main <pr-head-sha> [<more heads…>]
  # origin/main   wiki=223 notes=223 preflight=yes base=7db4ac99 verdict=indexed
  # a9fe2fc9      wiki=222 notes=221 preflight=no  base=5a367d42 verdict=SHORT by 1 note(s)
  # 2bf9483f      wiki=210 notes=0   preflight=no  base=0ddfda8b verdict=MISSING-DIR (…rebase, do not hand-add)
  ```
  It prints `indexed` / `SHORT by N` / `MISSING-DIR` / `EXTRA` plus the merge-base per ref, so one call
  classifies a whole sweep: `MISSING-DIR` means the branch predates `docs/changes.d` entirely (rebase),
  `SHORT by 1` is the single missing-note shape, and equal counts on a branch but red on `main` means the
  red is real. Its fixture form is `pytest -q scripts/test_pr_watch.py`. Fall back to the raw loop only
  when the script is unavailable:
  ```bash
  for r in origin/main refs/remotes/origin/pr<n>; do
    printf '%s notes=%s rows=%s\n' $r \
      "$(git ls-tree -r $r --name-only | grep -c '^agent-wiki/.*\.md$')" \
      "$(git ls-tree -r $r --name-only | grep -c '^docs/changes.d/.*\.md$')"
  done
  git cat-file -e refs/remotes/origin/pr<n>:docs/changes.d/<expected>.md && echo present || echo absent
  ```
  Equal counts on `main` + one short on the branch + the file absent on the branch ⇒ **stale base**: say
  "rebase, don't edit" and place no hold (a rebase needs no issue). Getting this wrong is a retraction-
  worthy error in the direction that accuses an innocent PR, so run the count *before* writing the
  verdict — and when you have already written it, retract on the PR with the two numbers, saying which
  of your own inferences was wrong, rather than quietly appending a correction.
- **A fix that greens previously-red tests must CORRECT the assertion, not delete it — read the test
  diff before you say "fixed".** Deleting or loosening the failing assertions turns the board green
  and the change wrong: those assertions are usually the correct alarm for an incomplete code change
  (a group of jobs removed from CI, but three of six test files reconciled). The correction shape is
  an assertion that still fails if the defect comes back — `assert callers["macos"] == (...)` becoming
  `assert "macos" not in callers` is fine; a deleted block, an added `xfail`/`skip`, or a widened
  `except` is a waiver. The same test applies to a repo rule the diff broke (an inline `python3` in a
  workflow `run:` step): satisfying it means moving the work into `scripts/` or a make target and
  calling that, never editing the rule's own test to permit it. In the verdict say which it was —
  "the six went green because each assertion was updated to the new contract and still reds if the old
  shape returns" — because "tests pass" is exactly what a deleted test also reports.
- **Check that a fix issue's acceptance command is the command CI actually runs.** An issue scoped to
  one module (`pytest tests/test_x.py -q`) can be satisfied while `make ci-unit` stays red — so every
  PR remains unmergeable and the lane has spent a push for nothing. Add the widening as a comment on
  the issue (all failing modules, then `make ci-unit` exit 0, then a completed `linux / unit` run quoted
  with its id) rather than silently reviewing against a criterion that cannot close the gate.
- **Build a comment body in a file, and read the published body back — not the post's exit code.** A
  `gh api … --jq "…\"$var\"…"` nested inside a double-quoted shell string collapses silently: the
  comment publishes with an empty field where the evidence should be, and `gh pr comment` still exits 0.
  Write the body with a heredoc into a file, post it with `--body-file`, then read back what landed
  (`gh pr view <n> --json comments --jq '.comments[-1].body'`); run any `--jq` that embeds shell
  variables as its own command and let Python do the formatting. **Quote the heredoc delimiter**
  (`<<'EOF'`, not `<<EOF`): an unquoted body expands every backticked span and `$var` as command
  substitution, so the published comment silently loses `fail=0` and `` `pipeline.yml` `` where the
  evidence should be. When one slips out, `PATCH /repos/<o>/<r>/issues/comments/<id>` with the corrected
  body and re-read it — note that `gh api … --jq .body` emits **raw text**, not JSON, so a `json.loads`
  round-trip fails; treat it as a string. A comment that renders a blank number
  is worse than no comment: it reads later as "nothing to report". When one does slip out, post a
  correction at the same sha naming the error and the real value rather than leaving the blank field
  standing.
- **`gh run list --commit <sha>` lags a fresh push; the API does not.** Minutes after a push it can
  report no runs for a sha that already has three, which reads as "CI never triggered" and invites a
  bogus empty commit. Ask the API instead:
  `gh api "repos/<o>/<r>/actions/runs?head_sha=<sha>&per_page=10" --jq '.total_count, [.workflow_runs[]|"\(.id) \(.name) \(.status)/\(.conclusion)"]'`.
- **`check-pr-authors` has no check name of its own — it runs inside `linux / unit`.** So
  "every listed check is green, the rest are pending" says nothing about attribution. Run it
  yourself on every PR, over the PR's own range:
  ```bash
  python3 scripts/check_pr_authors.py check --base origin/main --head HEAD
  ```
  A commit authored `Asimov Agent <agent@asimov.invalid>` (or `asimov-agent`,
  `github-actions[bot]`, `Hermes Agent`, …) is outside the allowlist and reds the unit job;
  only `Andy Holst <andy.holst@protonmail.com>` and `Asimov Agent <support@docondee.com>`
  are allowed, name AND email. Repair is the gate's own prescription and rewrites no work —
  `git commit --amend --no-edit --reset-author` (author+committer set to the allowed pair),
  `git push --force-with-lease` on the PR's own branch, then prove the tree did not move
  (`git diff <old> <new>` empty) and re-run the check for `OK`. A whole agent fleet can share
  one bad git identity, so check every PR in a batch before believing any of them is green.
- **An author-gate red naming commits that are not the PR's is a range bug, not a rebase.** When CI's
  `guard`/`check-pr-authors` fails and the named shas are `main`'s own merges, do not tell the lane to
  rebase — rebasing onto the newer base is exactly what pulls those commits into the scan. Reproduce the
  **CI shape** and the **PR's own shape** side by side:
  ```bash
  git fetch origin refs/pull/<n>/head refs/pull/<n>/merge
  # CI: PR's recorded base sha .. the merge ref (a pull_request head IS the merge commit)
  python3 scripts/check_pr_authors.py check --base <pr-base-sha> --head refs/pull/<n>/merge   # reproduces the red
  # the range the PR actually owns
  python3 scripts/check_pr_authors.py check --base origin/main   --head refs/pull/<n>/head    # usually OK
  ```
  `ci.yml` passes `PR_BASE = github.event.pull_request.base.sha`, so `<base>..<head>` sweeps everything
  the base branch gained after that sha. The fix is the range start (`mb=$(git merge-base "$PR_BASE" "$PR_HEAD")`),
  which is what `check_pr_authors.py`'s own docstring claims the scan is. Also check the default branch
  before blaming any PR — `git log -6 origin/main --format='%h %an <%ae>'` and
  `--base <old-tip> --head origin/main`: a missing surname there is enough to red every PR at once, and
  re-authoring `main` is a history rewrite that stays the owner's call.
- **A `docs/changes.d/<x>.md` fragment must link an `agent-wiki/<name>.md` note that exists on the
  SAME branch — `check-docs` reds otherwise, and it catches it before you can commit.** The fragment is
  a one-row index entry whose `Record` cell points at an `agent-wiki/` note; `changes-index` asserts that
  note is present, so creating a fragment on a branch that does not carry the note (e.g. you draft a
  change-record on the reviewer's own branch but the note lives only on the PR-under-review's branch)
  fails with `[changes-index] ERROR: docs/changes.d/<x>.md: links agent-wiki/<name>.md, which does not
  exist`. Always run `make check-docs` (or `make changes-index`) over the exact branch before committing
  the pair — a fragment with a dangling note reference is a red gate, not a record. When the note lives
  on another branch, either add the note here too or do not create the fragment; never leave a
  note-less fragment behind.
- **When your local branch has diverged from the fork ref you mean to update, push to a DISTINCT branch
  — never force over a shared/foreign branch lineage.** A reviewer's record commits often build on
  `main`'s history while the fork branch (`fix/…`, `reports/…`) still carries the earlier review-record
  lineage, so `git push fork <branch>` is rejected non-fast-forward and `--force` would discard the
  remote lineage. The safe move is `git branch <new-name> HEAD && git push fork <new-name>` — a fresh
  ref that carries your commit without rewriting anyone else's — then verify with
  `git ls-remote fork refs/heads/<new-name>`. Confirm ancestry first (`git merge-base --is-ancestor
  <remote-sha> HEAD`); if it is NOT an ancestor, they diverged and a force is the wrong tool.
- **`check-quant-catalog` reds every PR when the live Hub search changes** (issue #769).
  Do not let an author fold that data regeneration into a feature/docs PR; it is its own
  change.
- Merge order matters: a docs census refresh and a PR that adds files cannot both be
  "current" — land the code PR first, then regenerate the census.

## Sweeping many red PRs in one pass

When the ask is "review every failing PR" rather than one dispatch, do not write and post each comment by
hand — the boilerplate drifts and one malformed body survives unnoticed:

**When the ask is *rebase every open PR* onto a moved `main`, not review — see
`references/rebase-sweep.md` for the per-PR order (head re-read via API, merge-base skip, the
`CHANGES.md`-regenerate conflict fix, the `--continue`-hang recovery). The one rule that decides a
whole sweep is decided BEFORE any push: a PR's head may live on the fork (`head.repo.full_name` =
`andyholst/llgenie`), and pushing its rebase to `origin` updates no PR while creating or wrecking a
same-named branch on the base repo. Read the head repo from the API and push to `fork` when it is the
fork; also note the PR-head API lags a fresh force-push (verify with the ref read, not the pull
object), and a `do-not-merge` label is left untouched through the rebase.**

1. **One evidence call per PR, batched.** `gh run view <id> --log-failed > /tmp/prlogs/<id>.log` for every
   failing run, then extract the failing test *lines* from the files
   (`grep -oE 'tests/[a-z0-9_]+\.py:[0-9]+: AssertionError' | sort | uniq -c | sort -rn`). Read the counts,
   not the whole 400 KB log — a repeated identical assertion 80 times is deterministic, not flake.
2. **Classify with one command, not per-PR prose.** `--changes-index` for the index family; for anything
   else compare against `origin/main`'s last **completed** CI run and say the sha it belongs to.
3. **Generate the bodies in Python, post with `--body-file`, read every one back.** A dict per PR
   (`n`, `sha`, `run`, failing lines, attribution line) fed through one template keeps the four required
   facts (sha, command, run id, `auto=none`) identical everywhere; then loop `gh api …/issues/comments/<id>
   --jq .body` and assert each contains its own sha and `auto=none`. Posting exit codes prove nothing.
4. **Report the grouping, not just the rows.** "N PRs, one missing note" is the finding a dispatcher can act
   on; N separate verdicts with no shared sentence is homework.

Mixed heads are normal and must be said: a PR can carry the shared-base failure **and** one of its own
(`CHANGES.md is out of date` plus two `test_engine_skills` assertions). Name both families and give the
rebase for the first, the code question for the second.

## Verdicts

- **Request changes / block** — a factual claim in the diff or body is false (stale census,
  a gate that does not do what it says), a gate is red for a reason the diff caused, the
  diff is out of scope, or secrets/permissions weaken.
- **Comment** — everything verified green with only non-blocking notes (doc omissions,
  nits, merge-order advice). State exactly what you ran and what it returned.
- **Nothing** — a PR whose head sha, checks and review state you already reported and that
  has not changed.

**A verdict is about a sha, so it expires; a cause is not, so post that once on the umbrella.**
When every head in a family has moved past the shas you read, do not post a late verdict dressed as a
review — freeze one head and judge it, or say nothing. What does not expire is the shape of the failure:
"these branches are short one index note against `main`'s count, merge-base `<sha>`, remedy is a rebase"
is true of any head that kept that base, so it belongs on the tracking issue and each lane can act on it
without a fresh measurement from you. Post the cause on the umbrella issue, the verdict on the PR, and
never the other way round.

When a peer lane says "re-measure from `<head>`, your finding does not reproduce here", **do it before
you defend it.** `git ls-remote origin refs/pull/<n>/head`, re-run the exact gate/check at that sha, and
if it is now green the finding was correct at the sha you read and is history — retract on the PR naming
BOTH shas (`stale-shas → current-head`, which one was wrong), never append a softening, and never let a
snapshot you no longer own stand where a lane will re-read it. A blocker list is a claim about a tree,
and a tree that has been repaired since your measurement is the one the current head describes. This is
the same re-measure in the direction that clears your own finding, instead of accusing a PR of one.

A green PR that still cannot move is a **defect in the merge path, not on the PR**: if
`mergeable=MERGEABLE` and the required run concluded green but `mergeStateStatus` stays `BLOCKED`
on `REVIEW_REQUIRED`, the approve step or its gate is at fault — report it against the automation's
own issue and leave the PR alone, rather than approving it yourself to unblock the queue (nobody here
may approve). Equally, never derive "green" from a job count that is still moving: a run with rows
queued or in progress has no verdict, and the pending row is often the deciding one.

## Evidence block to include in every review

Numbers and exit codes, from your own run: the gate command + exit code, the failing or
absent engine/cell names, the test count, the doc gate line (`[check-docs] ok: …`), and the
CI verdict with the run id. Quote `gh` output, never paraphrase "CI looks green".

When the verdict is going to a merger, make it one sentence they can act on, either way:

```
green at <sha>, run <id>, N success / 0 failure / 0 cancelled, mergeable
either: not green, because <job> failed at <sha> in run <id> — <cause or "cause unreadable while in progress">
```

`cancelled` counts are part of that sentence, never omitted: a cancelled row is the difference between
"verified" and "no verdict", and a merger reading only success/failure cannot see it.

## Scheduled watch

`scripts/pr_watch.py` in this profile prints a deterministic fingerprint of every open PR
(head sha, review decision, merge state, labels, check buckets, comment count, the latest review
as `reviewer=<login>:<STATE>@<date>`, and the newest run at the head as
`runs=<wf>:<id>:<status>/<conclusion>|…` — every run at the head, because a verdict must cite the
`CI` id *and* the `scope`/`docs` ids beside it, so none of them has to be looked up by hand). Use it as a cron `monitor` script so
the agent is only woken when something actually changes; a diff in its output is the
trigger. It deliberately ignores *who* commented, so a hold that disappeared shows up as a
`labels=` change — and it prints

    WARN: APPROVED with no do-not-merge hold by <login> — verify a human made it
    ACTION: failing and unheld by <login> — review it or place do-not-merge with a reason
    UNVERIFIED: 0 checks and no run at this head — a non-main base gets no workflow, …
    NO VERDICT: the CI run at this head ended cancelled — …needs a fresh run at a frozen head, not a fix

when an approval exists without the hold, which is exactly the shape of an agent approval
under the owner's token. Prove the guard without waiting for a real incident:
`python3 scripts/pr_watch.py --selftest` (fixture checks, exit non-zero on failure).
The selftest also exercises the tree-side checks without needing a checkout: it swaps in a fake
`git` and asserts `--changes-index` marks a `docs/changes.d`-absent tree `MISSING-DIR` (never
`indexed`) and that `--soul-shrink` runs with no live profile — so a regression that makes the
discriminator call a clean tree `indexed` reds the selftest, not just the pytest module.

`python3 scripts/pr_watch.py --fingerprint` prints the sha256 of the exact bytes the monitor
hashes, so it can be compared with `monitor_state.last_output_hash` from
`cronjob_manage action=list`: equal ⇒ the next tick is skipped, different ⇒ the state really
moved. **A hash difference between two runs is not proof the script is flaky** — CI checks
complete between invocations, which is precisely the event the gate exists to catch. Diff the
two outputs (`python3 pr_watch.py > a; sleep 1; python3 pr_watch.py > b; diff a b`) before
touching the script; byte-identical across five consecutive runs on a quiet board is the
determinism proof. Verify the pipeline end-to-end from `cron/executions.db`
(`status`, `delivery_outcome`, `finished_at`), not from the scheduler's promise.
**After you *change* the script, prove determinism over frozen inputs, not over the live board.**
A two-run `diff` on a live board differing is the *expected* non-flakiness case (a check completes
between the ticks), so do not chase it as a regression. The proof that your new argv path is stable
is to feed it the same refs twice and diff those — `--changes-index origin/main <sha>` twice and
`--soul-rules <ref>` twice must both `diff -q` empty with `exit 0`. State that you measured frozen
inputs, and say the live/two-run diff is the documented exception, so a reviewer reading your
verification does not mistake an expected board movement for a broken script.

The first three lines are fixed and in this order: `workflows: active=N (names) disabled=M (names)`,
then `main: <sha> CI <status>/<conclusion> [FAILED:<jobs>]`, then the queue. The `main:` line exists
because a PR's red only means something against the baseline it was judged on: one red `main` can make
a whole sweep of PRs look red, and `main`'s own runs get cancelled by successive merges, so read it as
"no completed verdict at the head" when it says `queued`, `in_progress` or `cancelled` — never as green.
When it reports `failure` it names the failing jobs, because "main is red" is useless to a lane
deciding what to fix.

The `workflows:` line is how the fleet pause shows up: the owner disables workflows (20
`disabled_manually` while paused), and nothing else in the
fingerprint moves when that happens *or when it is lifted*, so this line is what makes the monitor
wake on a resume. The **names** are in it deliberately (short slugs, sorted) because "5 came back"
and "the 5 that came back are the ones my work depends on" are different facts; the **delta** is
deliberately NOT in it, because a value depending on the previous run would make two ticks differ on
an unchanged board and fire every tick. The agent diffs this line against its own previous output
(`continuity`) and reports `disabled 20 → 0, came back: auto-merge, fix-bot, …`.
While paused the job is monitor-only: report deltas with run ids, take no action.

`python3 scripts/pr_watch.py --changes-index <ref…>` is the branch/base discriminator described under
"Several PRs failing the identical assertions": it counts `agent-wiki/*.md` against `docs/changes.d/*.md`,
checks the preflight note, and prints the merge-base and a verdict per ref (`indexed` / `SHORT by N` /
`MISSING-DIR` / `EXTRA`). It shells out to `git` through an injectable `git()` so the tests need no clone;
keep that seam when editing it — a test that stubs the wrong argument position passes against a broken
implementation (a fixture reading `args[1]` where the real call puts the path in `args[-1]` reports a
false failure; fix the fixture, never the code it misrepresents). Defaults to `origin/main` with no refs.

`python3 scripts/pr_watch.py --soul-rules <ref>` is the per-lane rule census described under "A rule
stated twice": it counts rules 13/14/15 in every `agents/<lane>/SOUL.md` at the ref and returns one line
per lane with `ok` / `ABSENT` / `DUPLICATED`. Run it before declaring a behaviour-tree PR reviewable —
the gate's regexes pass a duplicated rule, so exit 0 is not evidence that each rule is stated once.

The fingerprint's contract is tested, not trusted: `pytest -q scripts/test_pr_watch.py`
(29 cases — identical state renders identical bytes, a held approval does not warn while an unheld
one does and names the approver, a red `main` names its failing jobs while a cancelled one says
"no verdict", `SKIPPED` is not a failure while `ACTION_REQUIRED` is,
`CANCELLED` is neither a failure nor a verdict, a cancelled CI run at the head raises
`NO VERDICT:` while a green or in-progress one does not, the workflow pause line counts
active/disabled, and `--fingerprint` hashes exactly what the plain run prints).
To measure the whole board rather than one PR (how many open PRs have a cancelled run at their
head, which were never gated at all, and — the other half — which recently merged commits had no
conclusion behind them), use `references/board-sweep.md`: the recipes and the arithmetic that turn
them into a citable number. The same file carries the **delegation census** — one `gh pr list` call
classified into `CONFLICT / RED / NO VERDICT / GREEN`, with the row format a dispatcher can assign
from — which is the right answer when the ask is "which PRs are red or conflicting, and who fixes
them" rather than "review this one".
Run it after any change to the script; a divergence between the printed and hashed
stream would make the monitor lie about whether the state moved.

### The two tree-side checks (`--soul-rules`, `--soul-shrink`)

When the ask is "can this `agents/` tree land?", one gate is not enough — the repo's
`check_agent_profiles.py` sees only shrinkage, and it is blind to a rule stated twice:

```bash
python3 scripts/pr_watch.py --soul-rules  <ref>   # per lane: r13/r14/r15 → ok | ABSENT | DUPLICATED
python3 scripts/pr_watch.py --soul-shrink <ref>   # per file: tree bytes vs live → LIVE-LONGER | LIVE-MISSING | ok
```

`--soul-rules` exists because a rule a lane does not state is a rule it cannot apply, and a rule
stated twice is two texts that drift (measured: `remedy.**` versus `remedy**` in the same file,
#922's family). `--soul-shrink` reproduces the gate's byte comparison from `git show` + the live
profile, so the two results can be cross-checked instead of trusted — run both back to back and
compare their finding sets. Report them as two verdicts — `ABSENT`/`DUPLICATED` for statements,
`LIVE-LONGER` for bytes — never as one "tree is wrong". `live=absent` is deliberately distinct from
`live=0`: a missing profile and a shrinking one are different fixes.

**This gate's result is `(PR head, live profiles at run time)` — it can go red under a PR nobody
touched.** The comparison reads files on the machine, so a peer lane editing its own live `SKILL.md`
mid-hour adds a finding to a tree whose head has not moved; a count taken ten minutes ago is a
sample, not a verdict. State the clock and the finding count together ("6 findings, 09:24Z"), re-run
immediately before reporting the tree as ready, and re-run again after the repair push — five findings
becoming six with the PR unmoved is the expected shape, not a contradiction. Do not carry an earlier
green forward as current, and do not tell a lane its gate "passes" without the time it passed.
