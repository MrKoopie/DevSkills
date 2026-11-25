---
name: build-and-test
description: Use to implement a planned change and verify its observable behavior with the project's own tools, entry points and applicable framework guidelines.
---

# Build and test a change

Start from the current combination in the [local feature workspace](../../references/feature-workspace.md). Record technical rulings in the execution ledger and user-directed deviations from the agreed plan in changes.md.

Start with the agreed requirements (with IDs when available) and technical plan. Reuse an independently
reviewed plan supplied by the caller. In the feature workflow, return missing
plan approval or a material change of approach to the planning step.

1. **Establish the baseline.** Read the repository instructions, status, relevant
   entry points, nearest tests and actual CI commands. Identify pre-existing
   changes so you can preserve them. Run the closest existing check and record
   its outcome. For a bug, reproduce the reported behavior at the affected
   boundary where feasible.
2. **Implement one observable outcome at a time.** Follow the existing path
   from caller to side effect. Reuse project conventions and the applicable
   implementation, UI and testing skills. Keep framework-specific decisions in
   the relevant framework skill. For structural changes, apply
   [refactor](../refactor/SKILL.md) to preserve the behavior already in use.
3. **Exercise the real contract.** Choose a check that would fail if the requested
   outcome were missing. Use the project's regular test suite. Add a focused
   regression test when current assertions miss the change. Exercise the normal
   entry point and the relevant failure or recovery path. For example, if a
   request rejects an invalid value, assert both the error and the resulting
   stored state. Verify existing consumers when changing a shared contract.
4. **Verify the candidate.** Run focused tests as each slice lands, then run
   the project checks affected by the combined change. Diagnose failures against
   the baseline, fix regressions and repeat the relevant checks after the final edit.
   For a check you cannot run, record the missing prerequisite and which outcome
   remains unverified.
5. **Hand off to the builder's review.** Identify the base, current revision
   and relevant local changes. For each requirement, summarize the behavior
   delivered, the check that exercised it and the observed result. Include exact
   commands, remaining failures and untested paths. In the feature workflow,
   continue with [self-review](../self-review/SKILL.md).
