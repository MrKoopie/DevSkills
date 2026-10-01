---
name: app-behavior-baseline
description: Capture and replay an existing application's user journeys, technical execution and dependencies with screenshots, diagrams and executable scenarios, or compare a candidate with that baseline before or during a rewrite.
---

# Capture or compare application behavior

Select capture, compare or both from the request. This skill owns evidence and
comparison rows; the invoking parent owns shared registers and readiness decisions.
When used alone, perform that parent role here. Baseline capture does not authorize
rewriting product code. Read the [artifact contract](../../references/artifacts.md).

1. Identify the source, agreed scope, repository/revision, existing changes, runtime,
   test runner and available browser. Distinguish actual configuration from defaults
   or inferred production settings. Record capability gaps without inventing evidence.
2. Enumerate routes/navigation, roles/permissions, commands, schedules, dispatched and
   undispatched jobs, listeners and inbound webhooks. Map every inventory entry to a
   flow/technical record or a reasoned exclusion. Reconcile discrepancies between
   source, documentation, tests and observed use. Unmapped entries prevent a claim of
   complete discovery; counts measure inventory coverage, not all possible inputs.
3. For UI surfaces, use [user flows](../../references/user-flows.md): actors, starting
   state, meaningful branches, actual screenshots, Mermaid and correlated backend
   effects. Cover normal, denied, invalid, empty, error/recovery and completed states
   where applicable. Browser unavailability leaves visual proof blocked; source
   inspection can continue.
4. Use [technical and dependencies](../../references/technical-and-dependencies.md)
   for CLI, scheduled work, queues, integration contracts, persistence, runtime
   requirements and external failure behavior. Give operations without UI their own
   records. Link technical and dependency IDs to the affected scenarios.
5. Before rewriting, implement and **run** the scoped executable scenarios following
   [baseline tests](../../references/baseline-tests.md). Prioritize browser journeys
   and business outcomes; supplement with feature/integration coverage and existing
   pure-rule tests. Store reusable tests in the project's normal suites and generated
   evidence locally. Capture a replayable product/test/fixture snapshot, not just hashes.
6. For compare mode, follow [comparison](../../references/compare-and-release.md).
   Execute the candidate against the shared cases and preserve the baseline. Return
   per-ID semantic and visual evidence, regressions, justified improvements and gaps.
   A passing mock or screenshot cannot establish downstream execution or data integrity.

Return the index, snapshot identity, mapped/excluded/unmapped counts, executed checks
and proof limitations. Keep records short and linked; load raw logs and screenshots
only as needed for the task or required verdict inspection. Optional independent
discovery uses the [delegation contract](../../references/delegation.md).
