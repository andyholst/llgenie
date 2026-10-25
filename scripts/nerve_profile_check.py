#!/usr/bin/env python3
"""Fail when a nerve SETTING targets a module the chosen PROFILE does not enable (issue #611).

WHY THIS EXISTS. A named nerve profile resolves its module set verbatim from
`hermes_nerve/profiles.py` (`modules = dict(PROFILES[name])`); settings do not switch modules on for a named
profile — the only pass that reads settings afterwards can turn modules OFF, never on. So an image can write
`context_engine_mode: apply`, `context_curation_mode: apply` and `gate_mode: advisory` while running the
`lean` profile, which does not enable `context_governor` or `action_gate`: the config looks configured and
the layer never runs. That is exactly how the bot image shipped "apply" curation and an advisory gate that
were both inert (issue #611, measured against hermes-nerve v0.3.1).

WHAT IT CHECKS. For every setting that only means something when its module is registered:

  gate_mode                != off            -> action_gate
  context_engine_mode      not in shadow,off -> context_governor
  context_curation_mode    not in shadow,off -> context_governor
  work_supervision_mode    != shadow         -> work_supervision
  nervous_enabled          true              -> nervous

Every module name above is the plugin's own id (`hermes_nerve/modules.py`).

HOW IT IS USED.

  * The agent image build calls it with the settings install_nerve_ci.sh just wrote, and the profile table
    the INSTALLED plugin carries (`$HERMES_HOME/plugins/nerve`), so a mismatch fails the build.
  * `make nerve-profile-check` runs `--self-test`: the same rule, on two synthetic profile tables, so the
    check's own behaviour (a full profile passes, a thin one fails and names the setting) is locked by
    `make test-unit` without needing a plugin install.

Exit codes: 0 = every active setting's module is enabled; 1 = at least one mismatch (or an unknown profile);
2 = the plugin's profile table could not be read.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

#: (setting, the module it needs, "is this setting asking that module to do something?")
RULES: tuple[tuple[str, str, object], ...] = (
    ("gate_mode", "action_gate", lambda v: v != "off"),
    ("context_engine_mode", "context_governor", lambda v: v not in ("shadow", "off")),
    ("context_curation_mode", "context_governor", lambda v: v not in ("shadow", "off")),
    ("work_supervision_mode", "work_supervision", lambda v: v != "shadow"),
    ("nervous_enabled", "nervous", lambda v: v in ("true", "1", "yes", "on")),
)

#: The keys this command knows about, in the order it reports them.
SETTINGS = tuple(key for key, _, _ in RULES)


def _norm(value: object) -> str:
    """`True`/`"TRUE"`/`"true"` are one answer, and so are `" off "` and `"off"`."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip().strip("'\"").lower()


def check(profile: str, settings: dict, profiles: dict) -> list[str]:
    """Findings for `settings` against `profiles[profile]`; empty means consistent.

    `profiles` is a plain `{profile: {module: bool}}` table — the plugin's `PROFILES` in the build, a
    synthetic one in the self-test. Business logic stays here: no caller re-implements the rule.
    """
    modules = profiles.get(profile)
    if modules is None:
        known = ", ".join(sorted(profiles)) or "(none)"
        return [f"unknown nerve profile '{profile}' — the plugin knows: {known}"]

    findings = []
    for key, module, active in RULES:  # type: ignore[misc]
        if key not in settings:
            continue
        if active(_norm(settings[key])) and not modules.get(module, False):
            findings.append(
                f"{key}={settings[key]!r} needs module '{module}', which profile '{profile}' does not "
                f"enable — the setting would be inert (written, and never read)"
            )
    return findings


def enabled_modules(profile: str, profiles: dict) -> list[str]:
    """The modules `profile` registers, sorted — what the build log prints so the run is readable."""
    return sorted(m for m, on in (profiles.get(profile) or {}).items() if on)


def _plugin_profiles() -> dict:
    """The INSTALLED plugin's own profile table (the image's `PROFILES`, not a copy of it)."""
    home = os.environ.get("HERMES_HOME", "/root/.hermes")
    sys.path.insert(0, os.path.join(home, "plugins", "nerve"))
    from hermes_nerve.profiles import PROFILES  # noqa: PLC0415 (import is the point: the real table)

    return {name: dict(mods) for name, mods in PROFILES.items()}


#: Self-test tables. Deliberately NOT copies of the plugin's: they are two shapes of a profile (one that
#: enables every module a setting can need, one that enables only the nervous system) used to prove the
#: rule fires in both directions without an install.
SELF_TEST_PROFILES = {
    "full": {module: True for _, module, _ in RULES},
    "thin": {"nervous": True, "action_gate": False, "context_governor": False, "work_supervision": False},
}


def _self_test() -> int:
    """Prove the rule: `full` accepts the image's settings, `thin` rejects them naming each module."""
    settings = {"gate_mode": "advisory", "context_engine_mode": "apply",
                "context_curation_mode": "apply", "work_supervision_mode": "advisory",
                "nervous_enabled": "true"}
    ok = check("full", settings, SELF_TEST_PROFILES)
    if ok:
        print(f"[nerve-profile] SELF-TEST FAILED: a profile that enables every module was rejected: {ok}",
              file=sys.stderr)
        return 2

    bad = check("thin", settings, SELF_TEST_PROFILES)
    missing = {"action_gate", "context_governor", "work_supervision"}
    named = {m for m in missing if any(f"'{m}'" in f for f in bad)}
    if named != missing:
        print(f"[nerve-profile] SELF-TEST FAILED: expected findings for {sorted(missing)}, got {bad}",
              file=sys.stderr)
        return 2

    # A shadow/off setting asks nothing of its module, so `thin` must accept those.
    quiet = {"gate_mode": "off", "context_engine_mode": "shadow", "context_curation_mode": "shadow",
             "work_supervision_mode": "shadow", "nervous_enabled": "false"}
    if check("thin", quiet, SELF_TEST_PROFILES):
        print("[nerve-profile] SELF-TEST FAILED: shadow/off settings demanded their modules", file=sys.stderr)
        return 2
    print(f"[nerve-profile] self-test OK: {len(RULES)} rules, both directions (findings: {len(bad)})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--profile", default="", help="the profile the image writes into the sidecar")
    ap.add_argument("--gate-mode", dest="gate_mode")
    ap.add_argument("--context-engine-mode", dest="context_engine_mode")
    ap.add_argument("--context-curation-mode", dest="context_curation_mode")
    ap.add_argument("--work-supervision-mode", dest="work_supervision_mode")
    ap.add_argument("--nervous-enabled", dest="nervous_enabled")
    ap.add_argument("--profiles-json", default="",
                    help="a {profile: {module: bool}} table instead of the installed plugin's (tests)")
    ap.add_argument("--self-test", action="store_true",
                    help="run the rule on two synthetic profile tables (the `make nerve-profile-check` mode)")
    a = ap.parse_args(argv)

    if a.self_test:
        return _self_test()

    if not a.profile:
        ap.error("--profile is required (or --self-test)")
    settings = {key: getattr(a, key) for key in SETTINGS if getattr(a, key) is not None}
    if a.profiles_json:
        try:
            profiles = {name: dict(mods) for name, mods in json.loads(a.profiles_json).items()}
        except (ValueError, TypeError, AttributeError) as e:
            print(f"[nerve-profile] --profiles-json is not a profile table: {e}", file=sys.stderr)
            return 2
    else:
        try:
            profiles = _plugin_profiles()
        except Exception as e:  # noqa: BLE001 — the reason string is what a build log needs
            print(f"[nerve-profile] cannot read the installed plugin's profile table: {e}", file=sys.stderr)
            return 2

    findings = check(a.profile, settings, profiles)
    if findings:
        print(f"[nerve-profile] profile '{a.profile}' does not register every module these settings need:",
              file=sys.stderr)
        for finding in findings:
            print(f"[nerve-profile]   - {finding}", file=sys.stderr)
        print("[nerve-profile] fix the profile or stop writing the setting (issue #611); the layer would be "
              "off with nothing visibly broken", file=sys.stderr)
        return 1

    print(f"[nerve-profile] profile '{a.profile}' enables: {', '.join(enabled_modules(a.profile, profiles))}")
    if settings:
        print(f"[nerve-profile] every active setting has its module: {', '.join(sorted(settings))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
