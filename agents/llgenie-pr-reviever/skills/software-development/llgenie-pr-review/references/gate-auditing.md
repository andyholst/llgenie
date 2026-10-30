# Auditing a gate: does the check actually enforce what it claims?

A gate that passes is not evidence it enforces anything. Most gate defects in this repo are the same
shape — **an invariant enforced on one side only** (one host, one directory, one direction of a
comparison) — and each one is a few commands from being proved or disproved. Audit the gate itself
before you trust its green, and name the *class* of blindness rather than the single instance, because
the next gate will have the same shape.

## 1. Ask what the check reads, not what it says

Open the implementation and look for the loop bounds and the direction of each comparison.

```bash
grep -n 'rglob\|iterdir\|glob' scripts/<gate>.py     # what tree does it walk?
grep -n '<the_live_side>.rglob' scripts/<gate>.py    # → nothing means that side is never walked
```

A comparison loop of the form

```python
for path in sorted(tree_profile.rglob("*")):
    counterpart = live_profile / path.relative_to(tree_profile)
```

authors every question as *"does this committed file differ from its live counterpart"*. It can never
ask *"does this live file exist in the tree at all"* — the direction that matters most for a
versioning gate. `0 absent-file findings` from such a gate is not evidence that everything is
versioned; it is the direction it cannot see. Count both sides yourself:

```bash
comm -13 <(git ls-tree -r --name-only <ref> -- <dir>/ | sed 's|^<dir>/||' | sort) \
         <(cd <live-dir> && find . -type f | sed 's|^\./||' | sort)
# these exist on the live side and NOT in the tree; the gate reports none of them
```

When the check *does* walk the other side, check what it walks it **for** — a live-side walk that
only collects secrets or forbidden paths is not an existence check, and adding a second walk for
existence is worse than reusing the first (a live-only file would then be reported twice, once as
`live-only` and once as a secret finding).

## 2. A same-scope static regex cannot see a call made through a helper module

A marker auditor that scans each test file for a network primitive **and** a host literal passes any
test whose fetch happens inside a helper imported at the top of the file: neither the primitive nor the
host string appears in the scanned scope, so the audit reports zero findings while the fetches run.
Prove it by asking the two questions the regex cannot:

```bash
# is the file even in the hermetic selection?
python3 -c "import sys; sys.path.insert(0,'scripts'); import unit_tests as ut; print('tests/<file>.py' in ut.select('.'))"
# is it excluded / deselected by the suite fixture?
python3 -c "import json; d=json.load(open('tests/fixtures/unit-suite.json')); \
print('tests/<file>.py' in d.get('excluded',{}), [k for k in d.get('deselect',{}) if '<file>' in k])"
# does the fixture really reach out, and to WHICH host?
grep -n 'sync(\|urlopen\|download\|requests\.' scripts/<the helper>.py
```

Also confirm the host the ruling names is the host the code uses — a fetch to a non-Hub endpoint is
invisible to a Hub-host regex by construction, so an acceptance criterion phrased "with the Hub
unreachable the gate must stay green" proves nothing about that file. Quote the resolved URL
(`python3 -c "import sys; sys.path.insert(0,'scripts'); import <helper> as h; print(h.UPSTREAM)"`) rather
than the host named in the discussion.

## 3. A gate can enforce a direction the product contradicts

When a fix rewrites a selector, check whether the *test* still describes the new contract or merely
stopped describing the old one. Two things distinguish a real fix from a silenced red:

- the assertion now states the rule and quotes the criterion or the published table that authorises it;
- the invariant the old assertion protected **still has a test somewhere**, ideally hermetic, so a
  semantic change does not arrive as a mere deletion.

Read the diff for deleted blocks, added `xfail`/`skip`, and widened `except` — all three turn a board
breen without fixing anything. A marker, an exclusion or a skip is a **selection** change: re-run the
test under its own pipeline (`-m network`, the excluded target) and confirm the verdict, not just the
collect.

## 4. The report shape

Name the class, the two commands that prove it, and the acceptance that closes it:

- the gate is blind in direction/host/scope `<X>` — proved by `<command>` → `<output>`;
- the negative control that would have caught it: add a live-only file, a non-Hub fetch through a
  helper, a second-direction comparison → **the gate reds and names the thing**;
- a no-regression clause pinning the existing findings' **keys and counts**, because the natural
  implementation of "walk both directions" can silently reclassify existing findings while the total
  count stays the same.

## 5. Verify with the check that GATES, not the CLI that resembles it

A repo can ship a CLI and a test suite that check the *same subject* and enforce **different
strengths**, and only one of them runs in `ci-unit`. Confirming a property with the CLI then proves
nothing about the suite — and the CLI is the one a human reaches for, because it is one command with
a readable verdict.

Measured: `scripts/check_docs.py check` returned **rc=0** on a change PR that added a
`docs/changes.d/` fragment and left `CHANGES.md` alone, so the fragment-only shape looked compliant
and several lanes were advised to adopt it. `ci-unit` then failed, twice, on:

```
tests/test_changes_index.py::test_the_real_index_renders_the_committed_changes_md
  assert committed == rendered, "CHANGES.md is out of date — run `make changes-index`"
tests/test_check_docs.py::test_the_real_tree_documents_every_user_facing_target
  assert set(info["changes_links"]) == {stem + ".md" for stem in info["wiki"]}
```

The CLI asked *"does `CHANGES.md` link a note that does not exist?"* (one-directional). The tests
asked *"does it link every note, and does the committed file equal the render?"*. Both are reasonable;
only the second gates.

**Rule:** before repeating "X passes", run the target CI actually invokes — `make ci-unit`, or the
named test file — not a neighbouring script with a similar name. If a CLI and a suite both exist,
quote which one produced the rc=0, and treat the suite as authoritative whenever `ci-unit` runs it.

Gate hygiene is never a `do-not-merge` reason: file the issue, link it into any verdict it touches, and
let the PR under review proceed.
