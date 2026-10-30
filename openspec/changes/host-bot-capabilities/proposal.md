# Pin each host llgenie bot to its lane tools and skills

## Why

The ten desktop Hermes profiles for llgenie share one config. None pins `platform_toolsets.cli`,
so every chat session inherits browser, computer use, image generation, and the rest of the
default tool list. Each profile also loads about 98 skills. `command_allowlist` pre-approves
`git force push` on every lane, including the reviewer. Nothing in the repository checks that
pin, so the next clone restores the wide set.

## What Changes

- `tests/fixtures/host-bot-capabilities.json` names the ten profiles, the cli toolsets, the skill
  names that stay enabled, and the one lane (rebase) that may keep the force-push approval.
- `scripts/host_bot_capabilities.py` applies and checks that fixture against a Hermes home.
- `tests/test_host_bot_capabilities.py` drives the module on a fake profile tree.
- The two HOST skills and `.hermes/skills/README.md` state the same pin.

## Impact

Host desktop sessions for the llgenie bots stop advertising tools and skills the lane does not use.
CI legs are unchanged: they still preload their own `.hermes/skills/<name>` with `hermes -s`.
SOUL files are not edited. The PR-watch monitor stays on #1037.
