---
name: implement
description: Use when implementing, fixing, or reviewing Laravel application behavior in models, actions, jobs, queries, policies, or Livewire components. Use the API or Filament specialist for work confined to those surfaces.
---

# Laravel implementation

Start with [project context](../../references/project-context.md). Preserve the
user's acceptance criteria and the existing application's conventions. Use
framework-native behavior and add abstractions only for a concrete responsibility.

## Implement or fix

1. Locate the closest existing operation and all affected entry points. Define
   the expected result, relevant rejection case, and side effects from the task.
   Reuse supplied criteria; clarify only a consequential unresolved decision.
2. For a behavior change, use existing tests or a focused regression that fails
   for the relevant reason before applying the correction. Follow the sibling
   [testing skill](../testing/SKILL.md) when designing or changing tests. A setup
   error is not proof of the intended regression.
3. Apply the smallest cohesive change. Use Form Requests and policies at HTTP
   entry points; preserve equivalent validation and authorization at Livewire,
   job, and CLI entry points as required by their trust boundary. Centralize
   invariants in the owning model or business operation. Put business workflows
   in owning actions even when a Filament page is the sole caller. In an existing
   or selected layered design, Application owns workflow orchestration and Domain
   owns its business rules.
   Do not create an action if it is just a model update or create; preserve
   validation and authorization on the native CRUD path.
4. Read only the relevant reference:
   [domain modeling](../architecture/references/domain-modeling.md) when creating
   or changing a domain component's contract;
   [idioms](references/idioms.md) for simplification;
   [data and tenancy](references/data-and-tenancy.md) for persisted invariants;
   [jobs and integrations](references/jobs-and-integrations.md) for asynchronous
   or provider work; [UI behavior](references/ui-behavior.md) for Livewire/Blade.
5. Verify with the shared [verification procedure](../../references/verification.md).
   If the task asks for an upgrade, follow the installed-to-target upgrade guides
   and compatible dependency constraints rather than replacing versions merely
   because a newer release exists.

## Review existing code

Trace changed behavior through callers and side effects. Check correctness,
authorization, tenant isolation, concurrent updates, and failure handling before
style. Confirm framework methods against the installed version. Report only
evidence-backed findings using the shared verification procedure; do not change
code during a review-only request.

Do not demand DDD folders, Pest, a new package, or a repository layer to perform
ordinary Laravel work. If a real ownership or extraction question arises, consult
the sibling [architecture skill](../architecture/SKILL.md). Read the
[API skill](../api/SKILL.md) for public contract changes and the
[Filament skill](../filament/SKILL.md) for panel behavior.
