# registry-sync carries the data, even when upstream lists a new engine (issue #683)

## Why

The weekly `registry-sync` job has landed no PR since 2026-10-13. A dispatched run on `main`
(`aa57657`) and the scheduled run `40313722697` both stop in the checks step:

```
[skills-validate] registry engine 'LemonSeed Engine' has no skill and no dated decision in
data/unsupported-engines.json (new and unresolved, issue #229) ...
[skills-validate] 16 skills, registry 40 engines, 16 error(s)
make: *** [Makefile:883: skills-validate] Error 1
```

Upstream's store grew from 23 to 106 models and from 8 to 40 engines. The job's checks step runs
`make skills-validate REGISTRY=data/models.json UNSUPPORTED=data/unsupported-engines.json` (#319),
whose contract is "every registry engine has a skill or a dated decision" — so the 16 engines
upstream just started listing kill the job **before** the two steps built for exactly that case:

- `make engine-skill-gap` — *reports* the new engines (must not fail; #219), and
- `make spawn-engine-skill-issues` — opens one tracking issue per NEW unskilled engine.

The result is a deadlock: the data that names the new engines never lands, so no tracking issue is
ever opened for them, so no decision or skill is ever recorded, so the data never lands. The header
of `registry-sync.yml` states the intended contract in words — "An upstream engine with no llgenie
skill is omitted from the offer; it does not fail this job" — and the job no longer honours it.

## What changes

1. **`scripts/engine_skills.py validate()` gains `allow_new_engines`** (CLI: `--allow-new-engines`).
   It still validates every skill against the registry (a skill whose engine vanished from the
   registry is still an error), and still errors on an engine with **no skill and no dated
   decision** unless the flag is set — in that case the engine is *named* and tolerated, because the
   sync's own next step turns it into a tracking issue. `ci-unit` keeps the strict form: the sync PR
   is red there until each new engine ships a skill or gets a dated decision, which is the reviewer's
   decision point (#229).
2. **`make skills-validate ALLOW_NEW_ENGINES=1`** forwards the flag; the Makefile help says what it
   is for and who may pass it.
3. **`registry-sync.yml`'s checks step passes `ALLOW_NEW_ENGINES=1`**, with the reason in the step's
   own comment: the sync must carry the data, the tracking issues carry the decision, and ci-unit
   carries the loud gate.
4. **`AGENTS.md`** records the split: a bot job that must carry data tolerates a NEW engine and opens
   its issue; only `ci-unit`'s `check-engine-skill-gap` refuses it.

## Impact

- `scripts/engine_skills.py` — `validate(..., allow_new_engines=False)`, `--allow-new-engines`.
- `Makefile` — `skills-validate` gains `ALLOW_NEW_ENGINES=1` → the flag; help text.
- `.github/workflows/registry-sync.yml` — the checks step, and the reason it is scoped that way.
- `AGENTS.md` — the new-vs-known engine split for a data-carrying bot job.
- `tests/test_engine_skills.py` — a new engine fails strict validation, is named and tolerated with
  the flag, and a skill whose engine left the registry still fails either way.
- `docs/BOTS.md` — the registry-sync section says which form runs where.
