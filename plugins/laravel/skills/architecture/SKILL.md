---
name: architecture
description: Use when designing Laravel boundaries, performing any refactor including small local changes, assessing package extraction, or reviewing architectural coupling. Scale architectural analysis to the change; a small refactor does not require redesign.
---

# Laravel architecture

Start with [project context](../../references/project-context.md), reusing known
facts. Select design, refactor or review mode from the request. Design produces a
proposal; it does not authorize migration. Read and apply the shared
[readable-design rules](../../references/readable-design.md) in every mode.
For every refactor, check the affected responsibility, caller and invariant before
editing; a brief retain/change decision is enough for a small local change.

## Establish scope and target

For module-wide design/refactoring, inspect an established relevant context.
Trace a complete workflow through entry point, application operation, domain
rules, persistence and integration where present. Cite classes, conventions and
weaknesses; explain what to follow. If no suitable context exists, state that
limitation and derive the target explicitly.

For module-wide work, map every requested capability and its models, workflows,
entry points, queries and integrations. Record current classes/paths, intended owner/path, move/retain/
defer, rationale, evidence and final status. Define namespaces and exceptions from
the user's scope, not just changed files. The user's selected structure takes
precedence over an existing convention.

For layered context design/refactoring, read the
[Company example](references/layered-context-example.md). Application coordinates
workflows; Domain owns business records, values and rules; Infrastructure adapts
providers. Entry-point placement follows the selected layout. Apply that layout
across the agreed scope; create only components with concrete responsibilities.

## Design

For component contracts and boundaries, read
[domain modeling](references/domain-modeling.md).

1. Explain which invariant each proposed boundary protects. Keep Eloquent inside
   the owning module; DDD does not require duplicate framework-free entities.
2. Prefer ordinary Laravel structure for simple work; introduce modules for
   cohesive ownership, not at an arbitrary model count.
3. Apply the shared action/query/DTO criteria; explain the concrete value of each
   retained or proposed boundary. Keep simple local behavior local and preserve
   cohesive operations where they improve understanding. In existing/selected
   layered designs, Application orchestrates workflows and Domain owns their rules.
4. Use contracts for genuinely varying implementations or meaningful business/
   provider boundaries, including one adapter exposing neutral outcomes.
   Reuse scopes/builders before repositories. Translate business outcomes into
   presentation messages at the UI/API edge.

## Refactor existing code

Read [safe refactoring](references/refactoring.md) for responsibility/namespace
moves. Preserve behavior and invariants through bounded slices. Package extraction
is a separate scope decision requiring consumer proof.

Before reporting completion, reconcile the original request and affected residual
code. For module-wide work, include the responsibility map and the reference's
completion audit; for a local refactor, use the brief retain/change decision.
Record retained legacy ownership, dependency exceptions and deferred work. Deferred agreed work means
partial completion unless the user agrees to reduce scope. Passing tests and
static analysis do not establish architectural completeness.

## Review

Check ownership, dependencies and placement against the agreed target. Explain
coupling with a concrete change scenario; unusual directories alone are not
defects. Use [verification](../../references/verification.md) for evidence/scope.

Consult [implement](../implement/SKILL.md) when code changes are requested; load
API or Filament only for affected contracts/presentation.

For module-wide work, deliver the comparison, map, dependency direction, exceptions
and proportional change/verification sequence, including CRUD/workflow entry points. Show each
integration's channel/provider, shared behavior and records versus business
records. Refactor/review results include completion evidence and remaining work.
A separate report file is not required for every edit.
