# 2026-10-27 — a new registry engine now reaches a bot with a file to write

Issue: [#757](https://github.com/asimov-agent/llgenie/issues/757) — PR: [#759](https://github.com/asimov-agent/llgenie/pull/759)

## What the chain was, and where it stopped

`registry-sync` copies upstream's store, `engine_skill_gap.py render` names the engines llgenie cannot
serve, and `spawn` files one tracking issue per new engine (#229). Then nothing: `ISSUE_LABEL` was
`bug`, while `scripts/issue_implementer.py` reads `agent:implement` then `agent:ready` — the open
spawned issues carried only `bug` (`#686` had to be labelled by hand). Even a correctly labelled issue
had no file to start from, because the image is generated from the skill
(`generate-engine-params` -> `containers/engines/params/` -> the `engine-image-*` matrix), so no skill
means no image means the engine is dropped by `rank_engines` and the models only it serves vanish from
the offer.

The second half — params, Dockerfiles, the CI matrix — was already automatic from a skill. The missing
half was the skill and the routing.

## What changed

- `engine_skill_gap.ensure_queue_label()` applies `agent:implement` **explicitly** after the create and
  reads the labels back; a label that does not land raises naming the issue. `open_issue()` repairs an
  existing unlabelled tracking issue, so a re-run fixes the older ones. The `--label` on create is not
  trusted, because #724 measured it being dropped on the CI token path (`#710`, `#749`: zero labels,
  exit 0).
- `scripts/engine_skill_scaffold.py` + `make engine-skill-scaffold ENGINE="<registry name>"` write
  `skills/engines/<id>/SKILL.md` from the registry's own entry (engine, repo URL, backends) and leave
  every unprovable key empty (`ref`, `pinned`, `license`, `formats`, `install`, `binary`, `detect`,
  `launch`, `health`, `alias_mode`, ...). A guessed pin is worse than an empty one because it builds;
  `engine_skills.validate()` treats empty as missing and names each key, so the scaffold is a loud
  to-do list. No overwrite without `FORCE=1`, no invented backend, no unknown engine.

## Verified

- `tests/test_engine_skill_scaffold.py` (6 cases) and the two label-routing cases in
  `tests/test_engine_skill_gap.py` — **82 passed** in `llgenie/test:latest`.
- `make lint`, `make check-wiring` (232 documents, the new script and test wired through `test-unit`),
  `make check-engine-skill-gap`, `make check-issue-bodies`, `make check-docs` green.
- A real scaffold run (`ENGINE="Ollama"`, `--id zz-test`, into a scratch dir) writes the file and the
  real `validate()` reports each empty key — the to-do list is the product's own error surface, not a
  separate invention.

## Deliberately not here

The upstream facts (a pin, apt packages, launch flags) are per-engine decisions read from that
project's repo — #686's work for the 16 current engines. #724 covers the same label drop for the
registry *change* issue.
