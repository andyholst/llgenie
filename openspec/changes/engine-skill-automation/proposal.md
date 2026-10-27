# engine-skill-automation — proposal

Issue: [#757](https://github.com/asimov-agent/llgenie/issues/757)

## Why

`registry-sync` carries every engine upstream lists into `data/models.json`, and
`make spawn-engine-skill-issues` (`scripts/engine_skill_gap.py spawn`) files one tracking issue per
engine llgenie does not ship (#229). The chain stops there, in two measured places:

1. **The issue reaches no bot.** `ISSUE_LABEL` is `bug`; the queue `scripts/issue_implementer.py`
   reads is `agent:implement`/`agent:ready`. The open issues the sync filed carry only `bug`
   (`#686` had to be labelled by hand), so nothing implements them. #724 measured that the label is
   also silently dropped on the CI token path (`#710`, `#749`: zero labels, exit 0, no warning), so
   "the create carried `--label`" is not evidence the label landed.
2. **There is no file to write.** The image `engine-image-*` builds is generated from
   `skills/engines/<id>/SKILL.md` (`make generate-engine-params` -> `containers/engines/params/<id>.json`
   + a Dockerfile per arch), so an engine with no skill has no image, and `rank_engines` drops it — the
   models only it serves vanish from the trend offer. A bot that does pick the issue up starts from a
   blank page and has to recall `scripts/engine_skills.py::REQUIRED_KEYS` from source.

The half that already works, and is not touched: once a skill exists, the params and Dockerfiles are
generated and the `engine-image-*` matrix in `pipeline.yml` builds and publishes every declared backend
with no workflow edit.

## What Changes

- **`scripts/engine_skill_gap.py`**: `QUEUE_LABEL = "agent:implement"`, `_issue_labels()`,
  `ensure_queue_label()`. `open_issue()` applies the queue label **explicitly** after the create
  (`gh issue edit --add-label`), reads the labels back, and fails loudly naming the issue when the
  label is absent. The same repair runs for an issue that already exists and lost it, so a re-run
  fixes `#686`-style issues instead of skipping them. `--dry` still mutates nothing.
- **`scripts/engine_skill_scaffold.py`** (new) + **`make engine-skill-scaffold ENGINE="<registry name>"`**:
  write `skills/engines/<id>/SKILL.md` from what the registry actually states — engine name, repo URL,
  backends (from `CUDA / ROCm / CPU / Metal`) — and leave every upstream fact it cannot prove **EMPTY**:
  `description`, `ref`, `pinned`, `verified`, `license`, `formats`, `upstream_watch`, `prereqs`,
  `install`, `binary`, `detect`, `launch`, `health`, `alias_mode`. `engine_skills.validate()` treats an
  empty required key as `missing`/`needs`, so the scaffold yields a loud, ordered to-do list rather than
  a plausible pin that builds the wrong thing. `ID=` overrides the kebab, `BACKENDS=` is required when
  the registry's wording names no backend llgenie knows, `FORCE=1` is the only way an existing skill is
  overwritten, `DRY=1` writes nothing.
- **`issue_body()`** names the scaffold command as the first fix step, so the bot that picks the issue
  up reads the exact command and the remaining checklist.
- **Tests** (real code, no mock of the product): `tests/test_engine_skill_scaffold.py` drives the real
  `scaffold()`/`skill_text()`/`backends()` and the real parser + `validate()` against a fixture registry
  file; `tests/test_engine_skill_gap.py` gains the label-routing cases through a `gh` executable on
  PATH (the external system only) whose `issue create` drops the label — the measured CI behaviour.

## Not covered

- Authoring the upstream facts themselves (a pin, apt packages, launch flags) stays a per-engine
  decision read from that project's own repo; the scaffold deliberately leaves them empty. The 16
  current engines remain #686's work.
- #724 (the same label drop for the registry *change* issue produced by
  `scripts/registry_change_issue.py`) is its own change; this one fixes the per-engine tracking issues
  the sync spawns.
- Making the sync itself unfrozen is #534/#673's territory.

Refs: #229 (the gap rule), #683 (the sync carries a new engine instead of dying), #724 (the measured
label drop), #686 (the engines this unblocks).
