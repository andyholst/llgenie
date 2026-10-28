---
name: bot-unattended
description: Use when you are running as an unattended llgenie bot leg — never ask, never wait, decide from the input and write the one file your own skill names.
version: 1.0.0
author: Asimov Agent
license: CC-BY-4.0
metadata:
  hermes:
    tags: [llgenie, bots, unattended, agent-leg]
---

# Unattended bot run

This skill is preloaded **alongside the bot's own skill** (`issue-triage`, `issue-refiner`,
`issue-dedup`, `issue-implement`, `architecture-doc`, `agent-fetch`, `rebase-conflict`, `pr-fix`).
That skill says what this run is; this one says how a run with nobody watching it must behave.

## Inputs

- The bot's own skill, preloaded in the same session. Read its **Inputs** section for the files and
  the step that produced them.
- `/repo`, the checkout this run may write. Nothing outside it exists for you.

## Output

- Exactly the file the bot skill's **Output** section names, in the shape it requires.
- Nothing else: no branch, no commit, no push, no PR, no comment, no issue. The deterministic step
  after you reads the file and does the GitHub write; it refuses an output that breaks the shape.

## Rules

- **Never ask a question, never wait for input.** `--yolo` approves shell commands and hooks; it
  does not answer your own `clarify`. In a detached run Hermes prints "Input required; detached
  without cancelling", exits 3, and the leg reports "changed nothing" — a wrong diagnosis for a run
  that never ran.
- **A genuinely open decision is not a question either.** Take the path that changes nothing
  (decline / distinct / already-clear) or the path that names what you checked (cited evidence), and
  say why in the output. Inventing a decision, or a close without evidence, fails the deterministic
  step and is worse than doing nothing.
- **Write nothing outside your skill's Output file.** A leg that touched the tree would have its
  edits committed by the job as if a human had made them.
- **Preflight before anything else (issue #792).** Your first action is `make bot-preflight`: it
  fetches `origin/main`, refuses a dirty or diverged tree (exit 2 — stop and say so, never work
  around it), fast-forwards a behind one, and writes `preflight.txt` with the line
  `AGENTS: <main sha> <bytes>b <lines>l` plus a digest of its `## ` headings. Re-read `AGENTS.md`
  in the tree the preflight proved — that copy is the rulebook this run obeys, not what you
  remember — and repeat the `AGENTS:` line verbatim in the artifact your own skill's Output names
  (the PR body, the brief, the report). A leg whose artifact carries no `AGENTS:` line is rejected
  by `make check-pr-hygiene`, so the line is not optional.
- **AGENTS.md still governs the repository.** This skill adds the unattended contract; it relaxes
  nothing there. Where the two meet, AGENTS.md wins.
- **A failing tool is reported, never worked around.** If a command you need fails, say what failed
  in the output and stop; never fake the result the output is supposed to carry.
