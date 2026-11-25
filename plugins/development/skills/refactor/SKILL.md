---
name: refactor
description: Use for behavior-preserving restructuring, from a local readability change to moving ownership across modules while preserving callers and stored data.
---

# Refactor existing code

For feature work, trace the preserved behavior to the requirements and prototype versions in the [local feature workspace](../../references/feature-workspace.md). Record any changed technical approach in the plan history.

1. Name the concrete friction and the desired structural outcome. Trace a real
   caller through the complete operation. Identify who owns the business rule,
   who changes state and what callers observe. For a local change, one sentence
   about ownership and the invariant is enough. For a module move, inventory all
   affected entry points and record the intended owner of each responsibility.
   Apply the project's architecture rules and the relevant framework skill
   for framework-specific ownership and compatibility decisions.
2. Establish a baseline at the public boundary. Inspect existing tests and run
   the closest checks before editing. Capture missing behavior with a focused
   characterization test when it could regress unnoticed. Include affected
   errors, persistence and external side effects. Separate any requested behavior
   change from the structural move so its expectation is explicit.
3. Compare retaining, simplifying and extracting the implementation against
   the actual flow. Prefer a local method for a readable local step. Extract a
   component when it owns a cohesive operation or invariant. Inline a pass-through
   when it only forwards data and all callers retain the same contract. For
   example, a lookup wrapper around data the caller already owns may disappear
   if authorization and freshness still hold at the new boundary.
4. Change one coherent slice at a time. Update registrations, callers, tests and
   configuration together. For renamed types or contracts check persisted names,
   serialized jobs and old clients. Preserve transaction boundaries, ordering,
   failure and retry behavior where they matter. Give any compatibility adapter
   a concrete consumer and removal condition.
5. Rerun the same baseline and applicable project checks. Search for old names,
   duplicate execution paths and stranded callers. Trace the resulting operation
   from the original entry point. Report what became simpler, which behavior was
   checked and any retained compatibility path or outstanding scope.
