---
name: pre-commit
description: Use before committing Laravel changes or reviewing commit readiness. Check new migration consolidation and Pint/Larastan availability and results.
---

# Laravel pre-commit

Inspect the staged diff and working-tree status. Follow project configuration and
keep changes within the intended commit. This skill guides assistant commits;
it is not a Git hook or authorization to commit.

1. **Migrations:** Review migrations created by this task, including earlier branch
   commits against the known base. Combine compatible changes only when they are
   unshared and unapplied in environments that must retain their identity. New Git
   files or local migration history do not prove this; if uncertain, report the
   candidate without rewriting it. Preserve dependencies, operation order, data,
   constraints and `up()`/`down()` behavior. Keep meaningful rollout boundaries;
   do not squash historical migrations or write to a database to establish status.
   After an authorized consolidation, verify forward and rollback equivalence in
   the project's isolated test database and recheck the diff without silently staging.
2. **Tools:** Inspect Composer declarations, lockfile, installed dependencies,
   scripts and configuration for `laravel/pint` and `larastan/larastan` (legacy:
   `nunomaduro/larastan`). Distinguish declared from installed. Confirm the Larastan
   extension loads; PHPStan alone is insufficient. Pint needs no custom config.
   Report missing or unusable tooling; installation requires task authorization.
3. **Checks:** Run existing Pint check and Larastan analysis commands when usable.
   Start with non-mutating formatting checks; keep fixes within scope and rerun
   affected checks after edits. Preserve analysis coverage, levels and baselines.
   Reuse verification only if it still covers the exact commit. Failed or unavailable
   checks remain unresolved; disclose them before any explicitly directed override.
4. **Report:** Give numbered results for migration consolidation, Pint and Larastan,
   with evidence and outstanding failures or unknowns. Do not claim readiness while
   required checks fail or remain unverified.
