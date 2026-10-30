# Evidence discipline: bases, heads, and the oracle

Depth notes for the rules in SKILL.md's evidence block. Load when a verdict or a finding is
contested, or when a branch has re-headed and the earlier measurement may no longer describe it.

## Which base to diff against

- **Stacked branch → its own base, not `main`, not the stack parent.** A cumulative
  `main...<branch>` diff includes every commit the parent carries, so the parent's files are
  attributed to your PR. Measured failure: a change-record file reported as "still modified" three
  times because the diff base was the repo tip rather than the sha the branch diverged from. Read
  the real base (`gh pr view <n> --json baseRefOid`), quote it beside the diff, and state the base
  in the finding itself — a finding is only meaningful against the base it was measured from.
- **Two bases, two answers.** If a peer reports a different file count or a different pass/fail,
  compare bases before comparing conclusions. Say which base each number came from rather than
  re-asserting yours.
- **A merge/precheck clean at a superseded base proves nothing.** When `main` moves, re-run
  `git merge-tree --write-tree refs/remotes/live/main <branch>` against the new tip before opening
  the PR. Run it against the immediately previous tip as well: clean against both means stable
  rather than lucky at one.

## Verdict expiry and the FAIL → PASS progression

- A verdict is bound to the sha it was measured at. Before restating "still red" or "still in-diff",
  re-read `pulls/<n>.head.sha` and re-run the control there.
- A FAIL at head A and PASS at head C is usually the branch **correcting its own expectation**, not
  a marker, a flake, or a hidden defect. Report the progression with both shas and both results, and
  retire the earlier wording instead of carrying it forward.
- A pytest marker is a **selection**, not a verdict. When a branch answers a red with
  `@pytest.mark.network` (or a roster exclusion), re-run under the marker's own pipeline
  (`-m network`), not only the hermetic one: a green `-m 'not network'` collect says nothing about
  whether the test passes. Marking legitimately moves a live-data test out of the hermetic gate; it
  must not be the thing that makes a red disappear.

## Grep forms and cited evidence

- **Grep BOTH call forms before reporting a fix absent.** A fix applied as a keyword
  (`fits(model, gb, ram, arch=arch)`) does not match a grep for the positional form
  (`fits(model, gb, ram, arch)`), and an empty result there is evidence the grep was wrong, not that
  the fix is missing. Read the commit's `git show HEAD -- <file> | grep -E '^\+'` and the live
  call-sites before claiming absence, and say which form you found.
- **Verify a decision's cited evidence is the row the code actually selects.** A ruling that says
  "the admitting X is Y" can be wrong about Y while being right that something admits: a selector
  that prefers the smallest qualifying candidate (card size, score, priority) can pick a different
  row than the one quoted. Enumerate the candidates and ask the function itself — print the selected
  row, its ranking field, and the floor it imposes — before writing the reason down. A fix made for
  the wrong row pins the wrong behaviour permanently. Also check the quoted fields exist: a cited
  `ran_on=8.0` is worthless if every entry carries `ran_on: None`.
- **The published document is the oracle when a test and the product disagree.** Parse the vendored
  source the gate claims to implement (a README table, a contract file) and report the item's
  position in it. If the doc places it where the product puts it, the expectation is stale and the
  branch is right; if the doc sides with the test, the product over-admits. This converts
  "over-admits or stale" into a fact the owner can act on, and stops a test rewrite from silently
  weakening an invariant that also lives in a hermetic test.
- **Contract vs run footprint.** When an admission uses a measurement's own hardware/RAM figure, the
  model's own declared minimum can be materially larger (measured: `system_ram_min 128GB` on the
  record, `32GB` named by the admitting run, floor computed as 32). That divergence decides
  admission and the summary check may not exercise it — name it as an open question rather than
  treating the green as covering it.

## Correcting your own posted text

- A mistyped sha, path or count in your own review comment is the same class of error this lane
  flags in others' work. Post the corrected value, name which was wrong, and keep the measurement
  itself — do not leave a wrong id standing as if it were a reading.
- When a refusal or a block is reported, quote the mechanism from the instrument's own log/source
  rather than guessing at intent; "the check is unsatisfiable because its inputs are prose tokens"
  is a different report from "the check is wrong".

## A null subfield is not an absent feature

`jq`'s `//` fallback fires on **null**, and many GitHub fields are objects whose interesting values
are nullable. So `--jq '.autoMergeRequest.commitHeadOid // "none"'` prints `none` for a PR whose
auto-merge is genuinely **armed** — `commitHeadOid` is null unless a head is pinned. That produced
a wrong board fact ("auto=none") about a correctly armed PR, in front of the lane that had armed it.

Print the whole object before concluding absence:

```bash
gh pr view <n> --json autoMergeRequest --jq '.autoMergeRequest'
# {"enabledAt":"…","enabledBy":{"login":"…"},"mergeMethod":"SQUASH"}   ← armed
# null                                                                    ← not armed
```

The general rule: **absence is `null` on the top-level field, never on one of its children.** A null
subfield means that attribute is unset, not that the feature is missing. The same trap applies to
`mergeStateStatus` vs `mergeable`, and to `check_runs[].conclusion` vs `.status` — `conclusion` is
null precisely *while* `status` is `in_progress`, which is why a run in flight must never be read as
a conclusion or as an absence.

