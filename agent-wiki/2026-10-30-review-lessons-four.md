# Four more review lessons: base rate before anomaly, render the render, predict from the tree, arm is not a head

The follow-up to #1105, recording lessons this lane learned after that PR was cut. Same rule as
before: each is here because a command changed a belief, not because it sounded right.

## 1. Measure the base rate before calling a pattern anomalous

A fixture showed a value identical across three backends and I called it impossible — "three
backends do not produce the same throughput to the decimal". One query refuted it: across the whole
file, **43 of 70** models served on more than one backend carry a constant `tps`, because the matrix
reports one measurement under every variant it offers. The pattern was the design.

The general rule: before reporting an anomaly, ask **how often the "anomalous" shape occurs in the
same data**. If the answer is a large fraction, you have found the design, not a defect. This cost a
public retraction on a PR whose author had already been told the finding was real.

## 2. A generated aggregate must be rendered and committed — and rendered after rebasing

`CHANGES.md` is generated from `docs/changes.d/`, and two tests assert it equals the render
(`test_the_real_index_renders_the_committed_changes_md`, and the `changes_links` clause of
`test_the_real_tree_documents_every_user_facing_target`). So a change PR must **render and commit the
render** — the fragment alone reds `ci-unit`, whatever `check_docs` says.

And the order matters: rendering reads the fragment set **on the base it reads**, so rendering before
rebasing writes rows where the old base put them, and the result conflicts with main's copy — the very
conflict the rebase existed to escape. Rebase, then render.

## 3. Predict a red from the tree instead of waiting for the matrix

When a matrix takes tens of minutes, the tree can often answer in seconds. Running the two named tests
against a PR's own checkout predicted its unit failure before the run concluded, and a clean-`HOME`
re-run ruled out host drift. Posting the prediction **with its retraction condition** ("if this lands
green I withdraw it with the run id") is what keeps it a prediction rather than a guess — and a
prediction that loses to a completed run has no standing.

## 4. `autoMergeRequest` is not a statement about the current head

`enabledAt` records a **time**, never a sha. Measured: a PR armed at `21:56:47Z` kept that timestamp
across **three** head moves, including one where the deciding gate had been cancelled and never ran.
So a reader sees "armed at 21:56" and cannot tell which head that referred to, nor that the arm
predates the head it now applies to.

Rule: report the arm **with the head it was set against**, and treat an arm older than the current
head as unverified rather than as intent to merge this one.
