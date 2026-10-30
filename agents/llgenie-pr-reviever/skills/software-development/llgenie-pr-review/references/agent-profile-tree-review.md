# Reviewing the `agents/` behaviour-tree PRs

Behaviour (SOUL.md + skills) is versioned in the repo under `agents/<profile>/`, one directory per
profile, indexed by `agents/manifest.json` and gated by `scripts/check_agent_profiles.py`. A PR in
this family claims to land *every* lane's instructions at once, so it is reviewed by counting and by
running the gate — never by reading the file list.

## The four commands that answer it

```bash
R=asimov-agent/llgenie
git ls-tree -r origin/main --name-only | grep -c '^agents/'          # is the tree on main at all?
ls "$(git rev-parse --show-toplevel)/agents" | grep -c llgenie      # profile directories at the head
python3 scripts/check_agent_profiles.py check                       # the gate: exit 0 or exit 1
make sync-agent-profile PROFILE=<profile> CHECK=1                   # compare tree vs live profile
```

`CHECK=1` prints `OK: N file(s) … match … byte for byte` when the tree copy equals the live profile in
`~/.hermes/profiles/<profile>/`, and names the first differing path otherwise. Byte-identity is the
contract: if you change a rule in the live profile only, that check starts failing, so **rule changes
go in the tree and are synced**, never the reverse.

## What the gate actually catches (quote the finding, not the exit code)

- a profile in the manifest with no directory, or a directory the manifest does not list;
- a profile directory with no `SOUL.md`;
- a skill whose frontmatter `name` disagrees with its directory, or has no/empty `description:`;
- a skill naming a `references/<file>.md` that is not in the tree;
- a secret-shaped value anywhere in the tree (it is read by an agent holding write credentials);
- a `SOUL.md` that stopped stating a rule the manifest declares for it — the checks are **regexes on
  the text** (`never\s+merge`, `do(?:es)?\s+not\s+implement`), so a paraphrase passes a human read and
  fails the gate;
- **`live-longer`**: the tree copy is shorter than the live profile (e.g. 4936 b vs 8596 b). That is a
  blocking finding, not a style note — `make sync-agent-profile` would *shrink* the live rulebook and
  no other check would notice.

## What the gate does NOT catch — count it yourself

**The comparison is one-directional: every loop walks the TREE and looks up the live counterpart, so a
file that exists only in the live profile is invisible.** Confirm before trusting a clean run:

```bash
grep -n 'rglob' scripts/check_agent_profiles.py          # the comparison loops
#   for path in sorted(tree_profile.rglob("*")):
#       counterpart = live_profile / path.relative_to(tree_profile)
grep -n 'live_profile.rglob' scripts/check_agent_profiles.py   # → nothing: the live side is never walked
grep -n '_text_files(base)' scripts/check_agent_profiles.py    # the one live walk: secrets/forbidden paths only
```

So "0 absent-file findings" is not evidence that everything is versioned — it is the direction the gate
cannot see. An unversioned skill reference on the host (behaviour that exists and was never committed)
produces no finding at all, while the same content one byte shorter than live does. When the question is
"is every lane's behaviour versioned?", count both sides yourself:

```bash
comm -13 <(git ls-tree -r --name-only <ref> -- agents/<lane>/ | sed 's|^agents/<lane>/||' | sort) \
         <(cd ~/.hermes/profiles/<lane> && find . -type f | sed 's|^\./||' | sort)
# lines here exist on the host and NOT in the tree — the gate reports none of them
```

Report that set explicitly ("tree 5 files, live 28, **17 live-only** — the gate names none") rather than
letting a green gate stand for two-directional coverage.

A rule stated twice is two texts that drift: one copy punctuates the bold, the other does not, and then
two lanes disagree about what the rule says (the same family as a rule satisfied by a quotation). The
gate matches a single occurrence and passes. Count per lane:

```bash
python3 scripts/pr_watch.py --soul-rules <ref>
# <ref> llgenie-<lane> r13=1 r14=2 r15=2 verdict=DUPLICATED r14,r15
# <ref> llgenie-<lane> r13=0 r14=0 r15=0 verdict=ABSENT r13,r14,r15
```

Three verdicts, not one: `ok`, `ABSENT` (a rule that lane cannot apply) and `DUPLICATED`. Repair a
duplicate by deleting the second block, never by reconciling the wordings. A lane whose file both
forbids and mandates the same action ("never run `gh pr merge`" beside "arm auto-merge") is escalated
with both line numbers: its own manifest rule contradicts the text while the gate stays green.

## Repairing a tree that fails the gate

Run the gate **at the PR head in a detached worktree**, not in the main clone:

```bash
git worktree add --detach ../llgenie-wt/g<n> $(git ls-remote origin refs/pull/<n>/head | cut -c1-40)
cd ../llgenie-wt/g<n> && python3 scripts/check_agent_profiles.py check; echo "exit=$?"
```

Quote the exit code **and** the finding lines. A `live-longer` blob is repaired by **diff and merge,
never `cp` and never "take the tree side"**: the live profile can carry whole sections the tree lacks,
so add the live-only lines to the tree copy and re-run until it prints `0 finding(s)`. Expect two
independent fixes at once — the shrink findings (exit 1) and the duplication/contradiction findings
(invisible to the gate) — and neither substitutes for the other.

## The gate is a sample, not a state

Half of its input is the local filesystem: each finding compares a tree blob against
`~/.hermes/profiles/<lane>/…` as it exists **at run time**. Another lane editing its own live skill
adds a finding to a tree whose head never moved, so a count from ten minutes ago is already history.

```bash
python3 scripts/pr_watch.py --soul-shrink <ref>    # independent reproduction from git show + the live files
# <ref> llgenie-<lane>/<path> tree=13362 live=13557 verdict=LIVE-LONGER
```

Run `--soul-shrink` and the gate back to back and compare their finding sets: a mismatch means a live
profile changed between the two calls. Report the count **with the clock** ("6 findings, 09:24Z"),
never as a property of the branch, and re-run after the repair push and again before anyone merges.
`LIVE-MISSING` (no live profile on this host) is a different fix from `LIVE-LONGER` (a real shrink) —
keep them distinct in the report.

## Verifying your own repair

Rewrite the file in a worktree you own, then verify the **committed blob**, not the working copy:

```bash
git add agents/<lane>/SOUL.md
git -c user.name='Asimov Agent' -c user.email='support@docondee.com' commit --amend --no-edit
S=$(git rev-parse --short HEAD)
for p in '<rule 13 clause>' '<rule 14 clause>' '<rule 15 clause>' '<rule 16 clause>' '<each standing rule>'; do
  printf '%s %s\n' "$p" "$(git show $S:agents/<lane>/SOUL.md | grep -cF "$p")"
done
```

`commit --amend --no-edit` without `git add` keeps the previous tree — the file you copied over it is
unstaged, every read of the working copy shows the new text, and the commit does not contain it. Count
every rule at the committed sha, including the ones the edit was not about: a condense that silently
drops an unrelated standing rule is the same defect as stating one twice, and only a per-rule count
sees it.

## A versioned copy of a live file goes stale on every edit — sync at open, not continuously

`CHECK=1` byte-identity means the tree copy must equal the live profile **now**. If the file you are
versioning is one you keep editing while the PR is held — a lane skill that gains a lesson on every
review pass — then each edit invalidates the branch, and the branch is a moving target that is stale
before it can merge (measured: five successive re-syncs in one evening, v1.17.0 → v1.22.0). Two
consequences:

- **Open the PR as soon as the tree path exists on `main`, and land later lessons as follow-up PRs under
the same issue** instead of re-syncing a held branch. If you do defer a sync, say the drift out loud —
"branch = the accepted slice at `<v>`, live is one lesson ahead, the diff is exactly that lesson" — never
leave "the branch matches live" standing after it has stopped being true.
- **`CHECK=1` exiting 2 with `TRUNCATED? … syncing would REPLACE N b of live behaviour` means the TREE is
the short side.** The fix is in the tree (re-copy the live file), never `make sync-agent-profile` — the
sync is one-way tree → live and would destroy live behaviour. Re-verify with `cmp -s` per file and quote
both sides' version and byte count; a green `check-docs` says nothing about this comparison.

## Review checklist

- [ ] count profiles at the head against the number of lanes the change claims;
- [ ] every lane has a SOUL file — a lane with no file is a hole, and a lane whose `SOUL.md` write was
      refused by the harness hands its **complete file body plus the `manifest.json` diff** over as a PR
      comment ready to commit verbatim (never routed around through `terminal` or a renamed file);
- [ ] the canonical rule block is present **verbatim** in every profile (a copy of a copy is where a
      rule shrinks);
- [ ] each rule is stated **once** per lane (`--soul-rules`, above);
- [ ] the declared rules are stated **literally**, per the regexes above;
- [ ] `check_agent_profiles.py check` exit 0 **and** its `N host-agent profile(s)` matches the directory
      count — exit 0 at two profiles is not evidence about a six-lane tree;
- [ ] no manifest entry without a directory and no directory without an entry (both are findings);
- [ ] `agents/` may not exist on `main` at all — a claim that "the tree is on main" is one
      `git ls-tree` away from being tested, and the tree usually lives in an open PR instead;
- [ ] both directions counted: every live-only file named (see "What the gate does NOT catch"), not just
      every tree file compared;
- [ ] `CHECK=1` re-run immediately before opening a versioning PR, with both byte counts quoted — a
      long-held branch is stale by default, and a green `check-docs` does not cover this comparison.

## Failure modes seen in review (all one command from being disproved)

- **Parallel copies of one unmerged tree.** Several lane PRs each carrying the whole skeleton plus one
  lane file are not a stack: the first to land conflicts every shared file, and a rebase then re-adds
  files that exist (resolving by taking either side silently drops a lane's manifest entry). The honest
  report is "one tree + N one-file follow-ups".
- **Stale copies of files `main` has since fixed.** A lane PR cut before a fix keeps the pre-fix version
  of shared test/workflow files; compare blob shas against `origin/main` before anyone rebases it with
  "our side", or the merge restores a defect that was already fixed.
- **A tree PR red on "missing index row" style assertions** while `main` is green — see the two-sided
  count in SKILL.md: usually a stale base, i.e. rebase, not edit.
