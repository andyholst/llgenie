# Tasks

- [x] `scripts/check_agent_profiles.py`: `shared_library()`, `installed_library_names()`,
      `_skill_dirs()` — the structural rule that separates a lane's own live skill from the library
      Hermes installs into every profile (bundle manifest, hub lock, the Hermes home's `skills/`,
      symlinks out of the profile).
- [x] `absent_from_tree_findings()` — walk live skill directories (a directory carrying `SKILL.md`)
      by the sync's own relative-path rule and emit ONE `absent-from-tree` finding per unmirrored
      directory naming the lane, the path and the file count.
- [x] Fix the 52-finding false positive: a Hermes CATEGORY directory under a tree profile's `skills/`
      is not a skill, so the file-level mirror follows the sync's relative path, not a bare directory
      listing.
- [x] `main()` prints an audible caveat when the profiles home exists but the shared library does not,
      instead of naming the whole library.
- [x] Tests in `tests/test_agent_profiles.py`: live-only directory, live-only directory beside a
      versioned skill, bundle/hub/shared library, symlink out of the profile, tree category is not a
      skill, the negative control through `main(["check", …])` (red naming the path, green once
      removed), the audible no-library skip, and `findings()` carrying the new shape.
- [x] `Makefile`: the `check-agent-profiles` `## help` line names the directory finding (no new target,
      so no wiring change).
- [x] Negative control on the host-scale fixture, both directions, with the gate's real exit codes.
- [x] `make check-agent-profiles` against the real host: the five lanes' live-only skill directories are
      named (one finding each), the library and the profile data are not.
- [x] `agent-wiki/2026-10-30-agent-profiles-live-only-skill-dir.md` + its `docs/changes.d/` row;
      `make check-docs` green.
- [x] `make openspec-validate NAME=agent-profiles-live-only-skill-dir` passes, and the scoped `ci-unit`
      gates (`check-agent-profiles` in the CI shape, `check-wiring`, `check-docs`, the unit suite) are
      green.
