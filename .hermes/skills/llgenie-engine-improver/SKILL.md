---
name: llgenie-engine-improver
description: Use when a trending engine needs syncing, a skill/params/image rebuilt, or an engine's serving params tuned on this host's GPU — the LLGenie engine loop.
version: 1.0.0
author: Asimov Agent
license: CC-BY-4.0
metadata:
  hermes:
    tags: [llgenie, inference-engines, docker, serving-params, trending-local-llms, cuda]
---

# LLGenie engine improver — the operating loop

This is a HOST skill: the `llgenie-engine-improver` profile runs it on a machine with a real GPU.
No CI leg preloads it (`HOST_SKILLS` in `scripts/check_agent_skills.py` admits it by name), so it is
versioned here beside the repo it drives, and the same body lives in that profile's own skill.

```text
trending-local-llms  data/models.json          (which engines + models trend)
        |  make sync-registry  -> llgenie/data/models.json
        v
skills/engines/<id>/SKILL.md                    (one per engine; the only place
        |  make generate-engine-params           build/serve facts may live)
        v
containers/engines/params/<id>.json + dockerfiles/<id>-<arch> + binaries.json
        |  check-engine-params / -coverage / -source ; engine-build.yml matrix
        v
ghcr.io/asimov-agent/llgenie/<id>:<hash>-<arch>   (published image per engine x arch)
        |  make engine-launchers
        v
~/bin/llgenie-engine-<id>  ->  scripts/llgenie_serve.py   (the picker the user runs)
```

Every link is generated from the one before. A break high in the chain shows up far down as "the
model vanished from the trend list" — always walk DOWN from the registry, never patch the symptom at
the bottom.

## Inputs

- The two checkouts: `trending-local-llms` (the store) and this repo, whose `data/models.json` is the
  vendored copy; `llgenie-wt` / `trending-local-llms-wt` for parallel branches.
- `make engine-skill-gap` — per-engine status: shipped, known-unsupported, NEW-AND-UNRESOLVED, plus
  the models that no shipped engine can offer.
- `skills/engines/<id>/SKILL.md` — the engine's pins, per-backend build recipe, binary, launch line.
- The host: `nvidia-smi` (card + driver), `docker` + the NVIDIA CDI entry, `nproc`, RAM. The tuned
  answer is a function of these, never of a remembered flag.
- The selected model row (repo, quant ladder, weights) from the vendored registry / live Hub.

## Output

- A reviewable PR (never a merge): the vendored store delta, the new or edited engine skill, the
  regenerated `params/` + Dockerfiles + `binaries.json`, the regenerated derived tables
  (`data/engine-skill-gap.json`, `data/trending-quant-catalog.json`, `tests/fixtures/trend-list-matrix.json`).
- For a tuning pass: the exact serving parameters, each traceable to a flag the pinned image itself
  prints in `--help`, plus the measured tokens/s of the run that justified them.
- A report that names the broken link, the command that proves the fix, and what still waits on CI or
  the user's merge.

## Rules

- Never merge, squash, auto-merge or push to `main`. Stop at the reviewable PR.
- **Never build an inference-server engine image locally.** CI builds and publishes every
  engine x arch cell; this host pulls and RUNS. No `make build-engine*`, no `docker build`, no
  source compile. A locally built image proves nothing about the artifact users pull, and a
  missing tag means CI has not published yet — not that you should build it.
- Never write a number, a flag, a pin or a version that did not come from real output. Report the
  blocking step and the alternative instead of a plausible guess.
- A generated artifact edited by hand is reverted by its `check-*` gate: land the change in the
  ENGINE SKILL, then regenerate.
- A new engine needs either a shipped skill or a DATED, REASONED entry in
  `data/unsupported-engines.json` read from upstream's own docs — never silence, never an inferred
  "no Linux support".
- Empty is better than guessed in a scaffold: a wrong pin or apt package BUILDS and hides the defect.
- Tune for weights + KV cache + batching reserve inside the card; a quant that fills the whole budget
  leaves nothing for context.
- Undo experiment side effects (containers, worktrees, clusters) before reporting.

## Step 0 — orient (before touching anything)

```bash
cd /home/asimov/repository/git/llgenie && git status --short && git log -1 --oneline
cd /home/asimov/repository/git/trending-local-llms && git log -1 --oneline
make engine-skill-gap          # shipped / known-unsupported / NEW-AND-UNRESOLVED
make engine-skill-gap-md       # same, markdown, for a PR/issue body
```

State the current HEADs and the gap before changing anything; the answer to "what is new" is that
report, never a guess.

## Step 1 — sync new/updated engines that have Linux support

- `make sync-registry` vendors the store into `data/models.json` + the contract and README. Report
  what changed with `make registry-change-report`, and file it with `make sync-change-issue`.
- The sync job is deliberately LENIENT (`--allow-new-engines`): a new engine lands even though it
  cannot ship yet, because a store that cannot land also cannot spawn the issue that resolves it. The
  STRICT gate (`make check-engine-skill-gap`) runs in the normal CI unit stage and is what reds until
  the engine is resolved.
- `make spawn-engine-skill-issues` opens one tracking issue per new unskilled engine; every such
  issue must name its FIRST command (the scaffold target with its `ENGINE=`/`ID=`/`BACKENDS=` knobs,
  then validate, then `generate-engine-params`).
- Ownership: the SYNC bot carries a new engine; the BUMP bot only re-pins engines that already have a
  skill (it derives from the skill, so it can never create one).

## Step 2 — skill -> params -> Dockerfile

```bash
make engine-skill-scaffold ENGINE='<registry name>' ID=<kebab> BACKENDS='CUDA / CPU' DRY=1
make check-engine-skill-gap
make generate-engine-params ENGINE=<id>
make check-engine-params check-engine-coverage check-engine-source
```

- Scaffold writes the facts the registry states and leaves everything unprovable EMPTY (`ref`,
  `pinned`, `install.<backend>`, `binary`, `detect`, `launch`, `health`, `alias_mode`, `license`);
  the validator turns empties into an ordered to-do list (`missing <key>` / `needs <key>`).
- A failed backend parse must FAIL LOUDLY with the offending string plus the explicit override —
  never default to CUDA (that is how a ROCm-only engine lands on an image nobody can run).
- Accepted build flags arrive only through the documented-params path (`engine-params-review` ->
  `-apply`), which requires the flag AND its quote to be in the engine's own file at the pinned sha.
- **The image matrix is derived from the params** — a new engine needs NO workflow edit.
- A `servable: true` skill with no container backend block emits NO params entry and NO Dockerfile,
  so it silently never enters the build matrix. After adding a skill, assert a Dockerfile exists for
  every declared backend.

## Step 3 — never build an engine image locally; pull the published one

**The engine BUILD belongs to CI.** `engine-build.yml` builds every engine x arch cell from the
committed params and publishes `ghcr.io/asimov-agent/llgenie/<id>:<hash>-<arch>`. This host does NOT
compile an engine: no `make build-engine` / `build-engine-base` / `build-engines`, no `docker build`,
no source checkout, no toolchain bake here. Local GPU time and disk are for RUNNING.

- After a params change, the local action is to wait for that CI cell and PULL:
  `docker pull ghcr.io/asimov-agent/llgenie/<id>:<hash>-<arch>`, or `make engine-launchers ENGINES=<id>`
  which resolves the exact tag the launcher will use.
- A missing tag means the CI cell has not published yet — check the workflow run. Never fall back to
  building it here: a locally built image is unverifiable against the pinned sha and diverges from
  what every user pulls, so a "pass" would prove nothing about the artifact that ships.
- Proof of an engine is the PUBLISHED image answering its own `detect` command with the pinned
  version — match a version shape (semver, or `pin <sha7+>`), never merely digits; a timestamped log
  line satisfies `\d+\.\d+`.
- A GPU-less CI runner cannot answer a `--version` that probes the device (`libcuda.so.1`
  ImportError); package metadata proves the wheels are installed, not that the binary runs — a weaker
  verdict, counted separately.
- The image TAG is derived from the params: edit a start/`pre_launch` step and the launcher resolves a
  tag that does not exist locally or in GHCR yet. Check `docker images` and the
  `engine-image-<id>-<arch>` job before saying "test it now".

## Step 4 — tune the serving params per engine on the real GPU (the core value)

1. **Discover the accepted flags from the image itself** at the pinned sha:
   `docker run --rm --gpus all <image> <binary> --help`, plus the fork's own `--help`/README section
   (forks rename and add flags).
2. **Fill the card, don't just avoid OOM.** Weights + KV cache + a batching reserve inside 16 GiB,
   then push context as far as the headroom allows.
3. **Per-engine, the levers differ** — verify names, never assume:
   - llama.cpp / Prism / forks: `--n-gpu-layers`, `--flash-attn`, `--ctx-size`, `--cache-type-k/-v`,
     `--batch-size`/`--ubatch-size`, `--parallel`, `--jinja`, `--no-mmap`, `--tensor-split`,
     `--threads`.
   - vLLM: `--gpu-memory-utilization`, `--max-model-len`, `--kv-cache-dtype`,
     `--enable-chunked-prefill`, `--max-num-seqs`, `--enforce-eager` (only when CUDA graphs break).
   - SGLang: `--mem-fraction-static`, `--context-length`, `--chunked-prefill-size`.
   - Ollama: `OLLAMA_FLASH_ATTENTION`, `OLLAMA_KV_CACHE_TYPE`, `OLLAMA_NUM_PARALLEL`, and `num_ctx`
     in the model parameters, not a flag.
   - Own-checkpoint engines (Strata, TensorFold, TensorRT-LLM): the plan function decides the
     quant/shards; the runtime args are the engine's own.
4. **A tuning claim needs a number from a real run** — `llama-bench` or the server's own reported
   timings, old vs new params on the SAME image, model and quant. No output, no number.
5. **Land the tuned value in the SKILL, then regenerate**; let the CI image cell rebuild and publish the new tag and PULL it (step 3) before running, so the proof is the shipped artifact.

## Step 5 — improve the picker and the trend selection

`scripts/llgenie_serve.py` (the `~/bin/llgenie` launcher) with `scripts/model_engine_pick.py`,
`scripts/trend_list_matrix.py` and `data/trending-quant-catalog.json` is the selection logic: how much
VRAM/RAM/arch -> which model -> which inference server -> which exact HF quant file.

- The offered-engine contract is per (model, engine): **offered <=> the engine has a runnable image
  for this arch AND some quant fits the weight budget**. A model can appear because ONE engine fits;
  report a skipped row WITH its reason, never as silent absence.
- Ranking keeps only engines with an image variant, so an unskilled engine drops its models out of
  the list silently — a registry problem (step 1), not a picker bug.
- Drive the grid as a reproducible command: `--vram V --ram R --arch A` override the detected host so
  CI can assert the permutation set. Test against the REAL vendored registry, stub only the Hub tree,
  and keep the file-existence check on the LIVE Hub (ranged 1-byte GET, 200/206).
- Regenerate the committed derived tables after a registry change:
  `make render-trend-list-matrix check-trend-list-matrix`,
  `make sync-quant-catalog check-quant-catalog`,
  `make render-engine-skill-gap check-engine-skill-gap`.
- The download must reuse the plan already shown to the user (same engine, same RAM budget) —
  recomputing defaults fetches a quant the engine refuses.

## Keeping this file and the profile skill identical

Repo copy: `/home/asimov/.hermes/profiles/llgenie-engine-improver/SKILL.md` (the installed skill:
`~/.hermes/profiles/llgenie-engine-improver/skills/software-development/llgenie-engine-improver/SKILL.md`)
carries the same loop. Change BOTH in the same change set: the repo copy is what a reviewer reads, the
profile copy is what actually loads on the host. Deep per-engine detail (hardware parameter mapping,
pin bumps, source conversions, matrix tests) stays in the profile's
`local-inference-engine-builds` skill — do not duplicate it here.
