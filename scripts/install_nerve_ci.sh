#!/usr/bin/env bash
# Install the Nerve plugin into the agent image's HERMES_HOME at BUILD time, and wire it the
# way the HOST runs it, per the plugin's own setup doc (issue #238).
#
# WHY the plugin at all. The plugin's JEV layer is what makes an autonomous bot CHEAPER and
# MORE ACCURATE: it answers the cheap decision calls (which step, is this the right edit, does
# this satisfy the check, is the turn even worth starting) so the expensive model calls are
# spent only where they are needed. The intended trade is MORE JEV CALLS, FEWER LLM CALLS — i.e.
# fewer tokens, better accuracy, and a faster run. A container that only runs `install.sh` has
# the Hermes CLI and NO plugin, so the bots get neither the decision layer nor its telemetry.
#
# HOW it is wired: `hermes plugins install` (the plugin), the host's settings under
# `plugins.entries.nerve.settings` (docs/SETUP.md: a value one level up is never read), and the
# PROFILE SIDECAR `${HERMES_HOME}/nerve/profile.json` — the host runs profile `lean`
# ("factory-first nervous system with token-heavy extras off": reflex, nervous, work_supervision,
# token_trajectory, receipts), and a named profile is what decides which modules register at all.
# The sidecar is written through the plugin's OWN `save_profile` (its validation, its atomic
# write), not by hand.
#
# The PROVIDER TOKEN is never here, and that is enforced, not merely intended: this script
# refuses to continue if a token-shaped env var is present at build time; the image knows only
# the NAME of the env var the plugin reads (TYPESAFE_API_KEY), and the run-time half
# (scripts/agent_jev_preflight.sh) reports whether the layer is available for THIS run.
#
# Everything is overridable so a maintainer can move the pin without editing the Dockerfile:
#   HERMES_NERVE_PLUGIN  owner/repo (or a Git URL)    default keeltrace/hermes-nerve
#   HERMES_NERVE_REF     40-char commit SHA           default the v0.3.1 release commit
#   HERMES_NERVE_PROFILE profile name                 default lean (the host's profile)
set -euo pipefail

fail() { echo "[nerve-ci] $*" >&2; exit 1; }

PLUGIN="${HERMES_NERVE_PLUGIN:-keeltrace/hermes-nerve}"
REF="${HERMES_NERVE_REF:-3de7d94982b7a2cb87c829e4b2366ced927d8fed}"   # keeltrace/hermes-nerve v0.3.1
PROVIDER="${HERMES_NERVE_PROVIDER:-typesafe}"

# `hermes plugins install --ref` takes exactly one immutable 40-character SHA: a tag or a
# branch would make the image hash-pin lie about what is inside it.
case "$REF" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
  *) fail "HERMES_NERVE_REF must be a 40-character commit SHA (got '${REF}'): a tag or branch would not pin the image" ;;
esac

HERMES_HOME="${HERMES_HOME:-/root/.hermes}"
export HERMES_HOME

# A token in the build environment would land in the image layers. Refuse, loudly, before any
# install work: the whole point of #238 is that the secret travels at RUN time.
for var in TYPESAFE_API_KEY OPENROUTER_API_KEY OPENCODE_API_KEY; do
  if [ -n "${!var:-}" ]; then
    fail "${var} is set in the BUILD environment: the provider token must arrive at run time (docker run -e ${var}), never in an image layer"
  fi
done

command -v hermes >/dev/null 2>&1 || fail "no hermes on PATH: install the CLI before the plugin"

echo "[nerve-ci] installing ${PLUGIN}@${REF:0:8} into ${HERMES_HOME} (provider=${PROVIDER})"
#
# THREE STEPS, NOT ONE (issue #585). `--yes-deps` made Hermes take a UNIVERSAL `uv lock` for the
# plugin's workspace: it resolves every marker split, not just this image's. The pinned plugin
# declares an OPTIONAL extra `laya = ["laya==0.3.3"]`, and laya requires `torch>=2.0.0`, which
# publishes no wheels for `python_full_version >= '3.14'` or `sys_platform == 'android'`. With no
# solution uv exits 1, Hermes refuses to admit the plugin ("Resolver: uv lock exited 1"), and so
# EVERY agent image build failed — which is every bot job, because `agent-jev-preflight` is the
# first step of each one (measured: run 40099608144 / job 120888884874).
#
# The extra is dead weight in THIS image, on two independent grounds: the bots run the plugin's
# default `reflex_backend` (`jev`) and this script writes no `reflex_backend`, so the Laya sidecar
# backend is never selected; and the plugin imports laya LAZILY, inside a function
# (`hermes_nerve/reflex/laya_service.py`), so an install without the extra still imports and
# serves jev. Adding `[tool.uv] environments` to the plugin's own pyproject does NOT help —
# measured against this exact pin: Hermes generates its own workspace and does not inherit it.
#
# So: clone without resolving (`--no-deps`), remove that one extra from the INSTALLED copy, then
# enable — which resolves a graph that now has a solution. The removal is ASSERTED, not assumed:
# a plugin that stops declaring `laya` fails the build and names this decision, because a silent
# pass would turn a deliberate scoping into a guess about what the next bump contains.
hermes plugins install "$PLUGIN" --ref "$REF" --no-deps
python3 - "$HERMES_HOME/plugins/nerve/pyproject.toml" <<'PY' || exit 1
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
if not path.is_file():
    sys.exit(f"[nerve-ci] {path} is missing: the bundle carries no pyproject to scope (issue #585)")
out, in_optional, dropped = [], False, False
for line in path.read_text().splitlines(True):
    stripped = line.strip()
    if stripped.startswith("["):
        in_optional = stripped == "[project.optional-dependencies]"
    if in_optional and re.match(r"^laya\s*=", stripped):
        dropped = True
        continue
    out.append(line)
if not dropped:
    sys.exit("[nerve-ci] the pinned plugin no longer declares a `laya` extra: revisit issue #585 "
             "instead of resolving its extras blind")
path.write_text("".join(out))
print("[nerve-ci] dropped the unused `laya` extra (laya==0.3.3 -> torch has no py3.14/android "
      "wheels, so a universal lock has no solution)")
PY
hermes plugins enable nerve

# The settings the HOST runs with (issue #238 records the host values verbatim). Hermes reads
# a plugin's options from plugins.entries.<id>.settings.<key>; a value written one level up is
# silently ignored and the plugin's schema default wins, which is why every write goes through
# the flat `hermes config set` path here (docs/SETUP.md of the plugin says the same).
set_setting() { hermes config set "plugins.entries.nerve.settings.$1" "$2" --force >/dev/null; }

set_setting jev_provider "$PROVIDER"
set_setting typesafe_model "${HERMES_NERVE_TYPESAFE_MODEL:-jev-latest}"
# The layer must decide the tool call, not let the model overrule it: the host sets `false`, and a model
# that can override the decision silently undoes the JEV call that was made to avoid a model call (#611).
set_setting allow_tool_override false
# The plugin's docs/SETUP.md "Nervous system defaults" block, verbatim: this is the RFC-ed
# decision architecture (the thing that makes the JEV calls), and `nervous_turn_admission` is
# part of it even though the plugin's schema default is already true — written explicitly so
# the image's config says what the run does instead of inheriting it silently.
set_setting nervous_enabled true
set_setting nervous_turn_admission true
set_setting nervous_mode correct_next
set_setting nervous_challenge_confidence 0.86
set_setting nervous_call_threshold 0.58
# `advisory` is the host's mode and the one a bot can live with: the pre-tool decision is logged and
# steered, never blocked, so a run still opens its reviewable PR. It only does anything when the profile
# registers the `action_gate` module — `operator` does, `lean` does not (issue #611); the check at the end
# of this script is what keeps the two from disagreeing.
set_setting gate_mode "${HERMES_NERVE_GATE_MODE:-advisory}"
set_setting gate_scope all
# Context curation is where prompt tokens are won: `apply` lets the Jev engine anchor safe
# candidates at the threshold, `shadow` only measures. Both default to `shadow` in the plugin
# schema; the host runs `apply`.
# The engine is the point: the plugin registers its own context engine (NerveContextEngine) and
# `apply` is what makes it the authoritative one. The schema default is `shadow`, which logs paired
# decisions and leaves Hermes' built-in compressor in charge - installed is not the same as set.
set_setting context_engine_mode apply
set_setting context_curation_mode apply
set_setting context_engine_register true
# Supervision is a policy decision, and under the host's `operator` profile its module is NOT registered:
# `shadow` is the honest value for a module that does not run (it measures nothing and asks nothing).
# Override it with `advisory|enforce` only together with a profile that enables `work_supervision`
# (`lean`/`marie_kondo`) — the check at the end of this script fails the build when the two disagree
# (issue #611).
set_setting work_supervision_mode "${HERMES_NERVE_WORK_SUPERVISION_MODE:-shadow}"

# The PROFILE SIDECAR (${HERMES_HOME}/nerve/profile.json) is the part that decides which modules
# register at all: the settings above only tune modules a profile turned on, and for a NAMED profile the
# module set comes verbatim from the plugin's PROFILES table — settings cannot switch a module on, the
# only pass that reads them afterwards can switch one OFF. The host runs `operator` (reflex, nervous,
# action_gate, context_governor, receipts, local_learning), which is the set the settings above are for:
# without `context_governor` the `apply` curation below never runs, and without `action_gate` the gate
# mode is inert (issue #611 — the image used to write exactly those settings under `lean`, where both
# modules are off). With no sidecar the plugin falls back to Legacy registration, so leaving it out
# would silently ignore the settings this script just wrote.
#
# It is written through the plugin's OWN `save_profile`, which validates the document strictly
# (version 1, known profile name, known module ids) and writes it atomically — a document
# invented here would be rejected at load time, and the plugin fails open to Legacy with only a
# log warning, i.e. the layer would be off with nothing visibly broken.
NERVE_PROFILE="${HERMES_NERVE_PROFILE:-operator}"
# The host carries the profile in BOTH places; the setting is what `hermes config get
# plugins.entries.nerve.settings.nerve_profile` answers, so the image's config says what the run does.
set_setting nerve_profile "$NERVE_PROFILE"
python3 - "$NERVE_PROFILE" <<'PY' || exit 1
import os, sys
sys.path.insert(0, os.path.join(os.environ.get("HERMES_HOME", "/root/.hermes"), "plugins", "nerve"))
from hermes_nerve.profiles import PROFILE_NAMES, load_profile, save_profile

want = sys.argv[1]
if want not in PROFILE_NAMES:
    sys.exit(f"[nerve-ci] unknown nerve profile '{want}' (expected one of: {', '.join(PROFILE_NAMES)})")
save_profile({"version": 1, "nerve_profile": want, "nerve_modules": {}, "advanced": {}})
loaded = load_profile() or {}
if loaded.get("nerve_profile") != want:
    sys.exit(f"[nerve-ci] wrote profile '{want}' but the plugin's loader reports "
             f"'{loaded.get('nerve_profile')}'")
print(f"[nerve-ci] nerve profile '{want}' selected, and verified through the plugin's own loader")
PY

# `plugins.entries.hermes-nerve.settings` is the DEAD pre-0.3.1 location: Hermes never reads it
# and Nerve warns about it at startup (docs/SETUP.md). A base image that carries it would look
# configured and do nothing.
if hermes config get plugins.entries.hermes-nerve >/dev/null 2>&1; then
  hermes config unset plugins.entries.hermes-nerve >/dev/null \
    || fail "could not remove the dead plugins.entries.hermes-nerve block"
  echo "[nerve-ci] removed the dead plugins.entries.hermes-nerve block (Hermes never reads it)"
fi

# YAML 1.1 reads the BARE token `off` as boolean false, and a boolean is not "off" to the
# plugin: `hermes_nerve/config_resolver.py` decides `action_gate = (gate_mode != "off")`, so a
# bare write turns the Action Gate ON — the opposite of the intent, and silently. The host's
# config carries the quoted string for exactly this reason. Normalise that one line, then prove
# the loaded value is a string.
GATE_MODE="${HERMES_NERVE_GATE_MODE:-advisory}"
python3 - "$HERMES_HOME/config.yaml" "$GATE_MODE" <<'PY' || exit 1
import pathlib, re, sys
path, want = pathlib.Path(sys.argv[1]), sys.argv[2]
lines = path.read_text().splitlines(True)
out, done = [], False
for line in lines:
    if not done and re.match(r"^\s*gate_mode:\s", line):
        indent = line[: len(line) - len(line.lstrip())]
        out.append(f"{indent}gate_mode: '{want}'\n")
        done = True
    else:
        out.append(line)
if not done:
    sys.exit(f"[nerve-ci] no gate_mode line in {path} to normalise")
path.write_text("".join(out))
PY

# Prove the image is what it claims to be: a bad pin or a plugin that landed under the wrong
# id would otherwise only surface inside a bot run, far from here. `hermes plugins list --json`
# is the machine-readable form: a grep over the Rich table would depend on the terminal width,
# and `grep -q` on a long pipe kills the writer with SIGPIPE (which `set -o pipefail` reports as
# a failure even when the name matched).
[ -f "${HERMES_HOME}/plugins/nerve/plugin.yaml" ] \
  || fail "the plugin did not land at ${HERMES_HOME}/plugins/nerve/plugin.yaml"
grep -q '^name: nerve' "${HERMES_HOME}/plugins/nerve/plugin.yaml" \
  || fail "the installed bundle is not the nerve plugin (plugin.yaml has no 'name: nerve')"
plugin="$(hermes plugins list --json 2>/dev/null | python3 -c '
import json, sys
try:
    rows = json.load(sys.stdin)
except Exception:
    rows = []
for row in rows if isinstance(rows, list) else []:
    if isinstance(row, dict) and row.get("name") == "nerve":
        print(row.get("status") or "", row.get("source") or "")
        break
')"
case "$plugin" in
  "enabled "*) ;;
  *) fail "nerve is not enabled in ${HERMES_HOME} (hermes plugins list --json reports '${plugin:-missing}')" ;;
esac
case "$plugin" in
  *"pinned@${REF:0:8}"*) ;;
  *) fail "the installed nerve is not the pinned commit ${REF:0:8} (reported: ${plugin})" ;;
esac
for kv in "jev_provider ${PROVIDER}" "typesafe_model ${HERMES_NERVE_TYPESAFE_MODEL:-jev-latest}" \
          "allow_tool_override false" "nerve_profile ${NERVE_PROFILE}" \
          "nervous_enabled true" "nervous_turn_admission true" "nervous_mode correct_next" \
          "nervous_challenge_confidence 0.86" "nervous_call_threshold 0.58" \
          "context_engine_mode apply" "context_curation_mode apply" \
          "context_engine_register true" "gate_scope all" \
          "gate_mode ${GATE_MODE}" "work_supervision_mode ${HERMES_NERVE_WORK_SUPERVISION_MODE:-shadow}"; do
  key="${kv%% *}"; want="${kv#* }"
  got="$(hermes config get "plugins.entries.nerve.settings.${key}" 2>/dev/null || true)"
  [ "$got" = "$want" ] \
    || fail "plugins.entries.nerve.settings.${key} is '${got}', expected '${want}' (a value written one level up is ignored, and a boolean is not the string it looks like)"
done

# And prove no secret is inside: the build refused a token above, and the config must not
# carry one either (the plugin takes the key from the env/secret scope, never from config).
if hermes config get plugins.entries.nerve.settings.typesafe_api_key >/dev/null 2>&1; then
  fail "the nerve config carries a provider key: the token belongs to the run-time secret, not the image"
fi

echo "[nerve-ci] nerve ${REF:0:8} installed and enabled; settings wired under plugins.entries.nerve.settings"
echo "[nerve-ci] provider key: run-time only (TYPESAFE_API_KEY) - scripts/agent_jev_preflight.sh wires it into the home"

# THE PARITY CHECK (issue #611). Everything above wrote settings AND a profile, and for a NAMED profile the
# module set comes verbatim from the plugin's `PROFILES` table: settings cannot switch a module on, the only
# later pass that reads them can switch one OFF. So a setting can be written for a module the profile never
# registers — `context_engine_mode: apply` under `lean` (no `context_governor`) and `gate_mode: advisory`
# under `lean` (no `action_gate`) are exactly that: configured on paper, off in the run. The checker reads
# the INSTALLED plugin's own table — not a copy of it — and fails this build when the two disagree.
python3 "$(dirname "$0")/nerve_profile_check.py" \
  --profile "$NERVE_PROFILE" \
  --gate-mode "$GATE_MODE" \
  --context-engine-mode apply \
  --context-curation-mode apply \
  --work-supervision-mode "${HERMES_NERVE_WORK_SUPERVISION_MODE:-shadow}" \
  --nervous-enabled true
echo "[nerve-ci] settings and profile agree: every active setting's module is registered by '${NERVE_PROFILE}'"
