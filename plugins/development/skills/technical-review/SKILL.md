---
name: technical-review
description: Use for an independent technical peer review of an implemented change against the functional request, repository guidelines and actual test evidence before UX validation.
---

# Independent technical peer review

Include the pinned requirements, prototype and plan from the [local feature workspace](../../references/feature-workspace.md) in the handoff. The coordinator records the independent verdict against the reviewed candidate.

The implementer prepares a handoff. A fresh native subagent performs the review
read-only. In clients requiring a named reviewer use `review-feature-implementation`.
Give it the original request, confirmed requirements (with IDs when available) and corrections, repo,
base and head, project instructions, and commands to run. Include staged,
unstaged and untracked work in the target identity (status, path and content
digest, plus staged blob identity if different). Share the technical plan as
context. Leave the verdict to the reviewer. If independent review cannot run,
report it pending.

## Reviewer's procedure

1. Read the request and repository rules first. For each requirement,
   identify its real entry point, trace the changed path to an observable result
   or side effect, and cite a check that would fail if the requirement broke.
   Look for omitted paths and extra behavior introduced without agreement.
2. Inspect the diff and affected callers, including existing consumers of changed
   contracts. Apply the project's actual conventions for ownership, framework
   primitives, readability and testing. For a disputed abstraction, trace the
   operation with and without it and identify the concrete responsibility or cost.
3. Probe risks introduced by this change. For example, trace unauthorized input
   through a changed write path, existing data through a schema change, or a retry
   after partial completion through a changed job. Explain the triggering condition
   and observable consequence. Distinguish a project rule from a preference.
4. Inspect assertions and fixtures, run the most relevant available tests and
   project checks, and distinguish observed results from prior logs. Verify the
   checkout still matches the handoff. State exactly what could not be exercised.
5. Return the reviewed revision and local snapshot identity, a short verdict for
   each requirement and applicable guideline, and findings in impact order.
   Each finding needs a file/location, rule or requirement, evidence, consequence
   and a verifiable correction. Give an overall verdict of pass, changes required,
   or unverified. A missing required check leaves the verdict open.

The implementer handles corrections and reruns affected tests. Return the new
snapshot and resolved findings to the independent reviewer for confirmation,
including interaction with previously reviewed code. Carry unresolved blockers
forward until addressed. The later UX audit retains its own scope and reviewers.
