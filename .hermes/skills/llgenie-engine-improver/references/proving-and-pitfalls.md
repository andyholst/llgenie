# Proving a fix, repo pitfalls, and versioning this skill

Extracted from SKILL.md to keep the always-on body small; load it when you are about to
prove a fix, hit one of these traps, or touch `.hermes/skills`.

## Reading a CI failure without the runner's log stream

`gh run view --log-failed` answers "still in progress; logs will be available when it completes" and
`gh run view --job <id>` returns 0 bytes with the pinned token — a CLI guard, **not** an API limit.
The API serves the log:

```bash
gh api repos/<owner>/<repo>/actions/jobs/<job-id>/logs --allow-escape-sequences \
  | sed 's/\x1b\[[0-9;]*m//g' > /tmp/job.log
grep -m1 'not published yet' /tmp/job.log | cut -c1-30     # first poll
grep 'not published yet' /tmp/job.log | tail -1 | cut -c1-30   # last poll -> budget actually spent
grep -c 'not published yet' /tmp/job.log                  # 90 polls x 20 s = 30 min, confirmed
```

That timing is what separates "the wait gave up too early" from "nothing ever produced the
artifact": 90 polls across exactly 30 minutes means the documented budget was honoured and the
producer job never ran — an ordering/capacity defect (#893), not a bad tag.

## Proving a fix, and cutting the branch it ships on

**Work in a worktree, never in the primary checkout.** `/home/asimov/repository/git/llgenie` is the
shared builder workspace other lanes treat as `origin/main`; commits parked there on a feature branch
make every other lane's tree ambiguous. Do:
`git worktree add ../llgenie-wt/<slug> -b <slug> origin/main`, work there, and keep the primary
directory on `main` and clean. **Push the branch as soon as it has one commit** (fork is fine for a
branch that needs no publish): an unpushed branch is a single copy on one disk, and a reviewable one
needs a remote to point at.

The repo's standard is "the new test fails on the parent, passes on the fix", and the checkout
you inherit is usually sitting on somebody else's PR branch. Both have a recipe.

1. **Isolate the change** — never commit onto an unrelated branch:

   ```bash
   git stash push -u -m "<what>" -- <files>
   git checkout -b <fix-slug> origin/main
   git stash pop
   ```

   Repeat per concern: one branch per defect, so a PR body and a reviewer see one thing.
2. **Prove the test is a real gate** — restore the parent's file, run ONLY the new test, put
   the fix back:

   ```bash
   cp scripts/<f>.py /tmp/fix.py && git show HEAD:scripts/<f>.py > scripts/<f>.py
   env HOME=/home/asimov RUNTIME=docker PATH="$HOME/llama-gguf-tools/.venv/bin:$PATH" \
     python -m pytest tests/test_<x>.py -q -k <new_test>
   cp /tmp/fix.py scripts/<f>.py
   ```

   A test that passes both ways proves nothing; the failing-on-parent run is the evidence the
   PR body quotes. The repo's own venv is required — bare `python3` has no `pytest`.
3. **Multi-line Python/YAML edits**: rewrite with `python3 - <<'PY'` doing an
   `assert old in text` then `text.replace(old, new, 1)`, and `ast.parse` afterwards. The
   `patch` tool mangles long block replacements in this tree.

## Pitfalls

- **The picker does not take a bare path as its model argument.** `llgenie /path/to/x.gguf`
  answers `No model matches '<path>'. Use --list`. Pass a substring (`llgenie Ternary-Bonsai`)
  or the explicit file flag (`--model-file /path/to/x.gguf`).
- **`--model-file` labels a LOCAL file with a REGISTRY model name and can pair it with the
  wrong engine.** A 0.5B GGUF was reported as the registry's flagship model and handed to
  SGLang, which wants HF safetensors, not a GGUF. Pin the engine with `--engine <id>`
  whenever you serve a local file, and treat the printed `Model :` line as unverified until
  it matches the file. A format/engine mismatch here is a picker defect to report, not a
  reason to hand-tune a command.
- **A GGUF needs a GGUF engine.** SGLang/vLLM/TensorRT-LLM serve HF weights; llama.cpp
  (and its forks), Ollama and the own-checkpoint engines serve GGUF. Passing a `.gguf` to a
  safetensors engine fails after a long load, not at parse time.
- **The `.gguf` extension does not say WHICH GGUF engine can load it.** A fork-only tensor
  type (Prism's `PQ2_0 = 142`, `PTQ1_0 = 143`) makes stock llama.cpp refuse the file at load
  (`invalid ggml type 142`) — discovered only after the container started, which reads as a
  hang. Read the header's tensor types (`model_engine_pick.gguf_tensor_types`, no dependency)
  before pairing a GGUF with an engine; the file's bytes decide, not its suffix.
- **Re-applying a patch blindly duplicates it.** After a revert or an edit round-trip the fix
  may already be in `HEAD`: check `git show HEAD:<file> | grep -c '<marker>'` before writing it
  again, and use `git checkout -- <file>` to get back to `HEAD`. Two copies of the same block
  still pass the tests, so nothing catches it.
- **A stale file IS the evidence — copy it before you fix it.** When a fault is proven by a file on
  disk (a stale launcher, a hand-edited params file, a drifted lockfile), `cp` it to `/tmp` (or the
  scratch dir) FIRST, then repair the host. Fixing first destroys the specimen a reviewer wants
  cited, and reconstructing it later is a reconstruction, not an observation. Two proofs are cheap:
  the artifact that failed, and the clean run after the fix.
- **An image tag hashes FOUR inputs, not just the params**: the variant's params, its committed
  Dockerfile, `containers/engines/entrypoint.sh` and `scripts/engine_runner.py`. Editing the runner
  (or the entrypoint) recomputes every engine's tag, so a launcher installed from another checkout
  legitimately reads as stale — classify drift as "pin moved" vs "one of the other three inputs
  moved" before blaming a pin.
- **A long backoff with no output is indistinguishable from a hang.** Any wait loop over the
  network (a Hub 429, a retry ladder) must print what it is waiting for and for how long, on
  stderr. A silent multi-minute park gets reported to the user as a broken tool.
- **"That branch was never pushed" is a claim about ONE remote.** Ask each remote before you accept
  it: `git ls-remote origin <ref>` and `git ls-remote fork <ref>`. A branch pushed only to the fork
  looks absent from `origin` and gets reported as a single copy on one disk; re-pushing "for
  insurance" then starts publish-capable CI nobody wanted. Check both, quote the one that answered.
- **A test failure that reproduces on `main` is not your regression.** Before attributing it, run the
  same file on the untouched checkout. Some files are host-only by design and refuse a bare run —
  their own assert names the make target that runs them
  (`…assert BACKEND …, "run through make <target> BACKEND=…"`). Report it as pre-existing with both
  runs quoted, never as "my change broke the suite".
- **A commit message or PR body must not invent an issue number.** If the work has no issue, or the
  number arrived later, drop the reference and write the summary — a wrong `#NNN` sends reviewers to
  unrelated context and cannot be retracted once quoted.

## Versioning this skill in the repo (the `.hermes/skills` gate)

The llgenie repo keeps agent contracts in `.hermes/skills/<name>/SKILL.md`, and
`make check-agent-skills` refuses any skill there that no `hermes -z … -s <name>` leg
preloads (`skill-unused`). A HOST skill — an operator loop that needs a real GPU, so no CI
leg can load it — is admitted by NAME via the `HOST_SKILLS` frozenset in
`scripts/check_agent_skills.py`, exempt from the unused rule ONLY: it still owes frontmatter
(matching dir name + description) and `## Inputs` / `## Output` / `## Rules`.

- Admit by name, never by shape — adding another one must be a reviewed diff.
- Never invent a leg (a `hermes -z` recipe) just to satisfy the gate: a fake leg is the dead
  weight the rule exists to catch.
- Two files, one change set: the repo copy is what a reviewer reads, the profile copy is what
  loads on the host. Patch both, and run `make check-agent-skills` before committing.
- Do not fabricate a PR/issue number in the commit subject or body. If no issue exists, write
  the change summary without one.
