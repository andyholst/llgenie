# 2026-10-27 — a new registry engine now reaches a bot with a file to write

Issue: [#757](https://github.com/asimov-agent/llgenie/issues/757) — PR: [#760](https://github.com/asimov-agent/llgenie/pull/760)

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

## Who runs it, and when — the bot, not the agent's memory

The scaffold is called by `scripts/issue_implementer.py dispatch` (`make issue-bot-dispatch`, the step
`issue-bot.yml` runs before the implement leg). It recognizes a tracking issue by the title
`engine_skill_gap.issue_title()` produces, runs `engine_skill_scaffold.scaffold()` for that engine, and
appends a `## Scaffold` section to `issue.md` naming the file, its backends and what is still empty. So
`skills/engines/<id>/SKILL.md` exists before the agent reads `issue.md` — the whole point of queueing the
issue is that the file, not the recollection of `REQUIRED_KEYS`, is what the implement leg starts from. A
dry dispatch writes nothing; a plain issue gets no section and no file; an engine the vendored store no
longer names is reported in that section (the issue is stale) instead of failing the dispatch.

The order, end to end: `registry-sync` (weekly) -> `data/models.json` carries the engine ->
`make render-engine-skill-gap` + `make spawn-engine-skill-issues` (queued, `agent:implement`, read back)
-> `issue-bot.yml` -> `make issue-bot-dispatch` writes the skill -> the implement leg fills the empty
keys -> `make generate-engine-params` -> `engine-image-*` builds and publishes per arch.

## Verified

- `tests/test_issue_implementer.py` (3 dispatch-scaffold cases), `tests/test_engine_skill_scaffold.py`
  (7 cases) and the label-routing cases in `tests/test_engine_skill_gap.py` — **126 passed** in
  `llgenie/test:latest` (the three files together).
- `make lint`, `make check-wiring` (232 documents, the new script and test wired through `test-unit`),
  `make check-engine-skill-gap`, `make check-issue-bodies`, `make check-docs` green.
- A real scaffold run (`ENGINE="Ollama"`, `--id zz-test`, into a scratch dir) writes the file and the
  real `validate()` reports each empty key — the to-do list is the product's own error surface, not a
  separate invention.

## Deliberately not here

The upstream facts (a pin, apt packages, launch flags) are per-engine decisions read from that
project's repo — #686's work for the 16 current engines. #724 covers the same label drop for the
registry *change* issue.

## The shared quant-catalog gate this PR also had to clear (#769)

`make check-quant-catalog` was red on `origin/main` itself (`ea80ab4`), not because of this change: the
committed `data/trending-quant-catalog.json` still carried six `SolsticeAI/Nanbeige4.3-33B-mlx-*` plans
(that repo now answers 401) and `ToPo-ToPo/Ornith-1.5-35B-A3B-mlx-4bit`, which the live Hub search no
longer returns. Both `linux / unit` and `macos / unit` on PR #760 failed there after 14545 tests had
passed. `make sync-quant-catalog` (the sanctioned generator) re-rendered the catalog and its fixture:
`make check-quant-catalog` -> `OK ... matches the generator` (89 models, 1611 links, 1 newly-added link
probed, 0 dead, 0 gated).

The underlying defect — the gate turning live-search churn into a repository-wide red, and a sync
dropping a still-public plan — is filed as **#769** and is not fixed here.
