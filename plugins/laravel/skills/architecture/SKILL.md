---
name: architecture
description: Use when designing Laravel domain boundaries, restructuring existing modules, assessing package extraction, or reviewing architectural coupling. Routine feature edits do not require an architecture redesign.
---

# Laravel architecture

Start with [project context](../../references/project-context.md), reusing known
facts. Select design, refactor or review mode from the request. Design produces a
proposal; it does not authorize migration.

## Establish scope and target

For module-wide design/refactoring, inspect an established relevant context.
Trace a complete workflow through entry point, application operation, domain
rules, persistence and integration where present. Cite classes, conventions and
weaknesses; explain what to follow. If no suitable context exists, state that
limitation and derive the target explicitly.

Map every requested capability and its models, workflows, entry points, queries
and integrations. Record current classes/paths, intended owner/path, move/retain/
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
3. Use actions for workflows, coordinated writes, external effects or reusable
   business decisions, even with one caller. Do not wrap bare create/update;
   retain validation, authorization and model invariants on direct CRUD. DTOs,
   builders and interfaces need justification. In existing/selected layered
   designs, Application orchestrates workflows and Domain owns their rules.
4. Use contracts for genuinely varying implementations or meaningful business/
   provider boundaries, including one adapter exposing neutral outcomes.
   Reuse scopes/builders before repositories. Translate business outcomes into
   presentation messages at the UI/API edge.

## Refactor existing code

Read [safe refactoring](references/refactoring.md) for responsibility/namespace
moves. Preserve behavior and invariants through bounded slices. Package extraction
is a separate scope decision requiring consumer proof.

Before reporting completion, reconcile the original request, responsibility map
and residual code using the reference's completion audit. Record retained legacy
ownership, dependency exceptions and deferred work. Deferred agreed work means
partial completion unless the user agrees to reduce scope. Passing tests and
static analysis do not establish architectural completeness.

## Review

Check ownership, dependencies and placement against the agreed target. Explain
coupling with a concrete change scenario; unusual directories alone are not
defects. Use [verification](../../references/verification.md) for evidence/scope.

Consult [implement](../implement/SKILL.md) when code changes are requested; load
API or Filament only for affected contracts/presentation.

Deliver the comparison, map, dependency direction, exceptions and proportional
change/verification sequence, including CRUD/workflow entry points. Show each
integration's channel/provider, shared behavior and records versus business
records. Refactor/review results include completion evidence and remaining work.
A separate report file is not required for every edit.
