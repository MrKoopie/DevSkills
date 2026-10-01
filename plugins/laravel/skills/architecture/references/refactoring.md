# Safe modular refactoring

## Scope and placement

Start from the original request and the established-context comparison, not just
the implementation's changed files. Inventory the capability's models, relations,
workflows, queries, provider interactions and entry points, including jobs,
commands and UI callers. Give each a target owner and namespace under the agreed
layout. Keep direct CRUD and intentional framework locations explicit.

Use these fields in the responsibility map:

| Capability | Current classes/paths | Target owner/path | Move, retain or defer | Rationale | Verification evidence | Final status |
| --- | --- | --- | --- | --- | --- | --- |
| Company assortment records | app/Models/Company/CompanyArticle.php and related records | Domain/Company/Models | Move | Company owns these records under the selected layout | Pending import/relation and behavior checks | Planned |
| Company notes | Livewire/Company/CompanyNotes.php | Application/Company/Livewire | Move entry point; retain direct CRUD | No workflow beyond validated, scoped, authorized writes | Pending caller and mutation checks | Planned |

These rows illustrate the map; discover the full scope in the actual repository.
Record a retained legacy owner with its reason. Temporary compatibility paths need
a removal condition. A deferral records unfinished work; only an agreed scope
reduction removes it from the requested deliverable.

## Move bounded slices

1. Establish the current behavior and caller graph before moving code. Preserve
   transaction boundaries, lock ordering, authorization, tenant scope, monetary
   precision, provider references, idempotency, and after-commit effects.
2. Give each module ownership of writes to its records. Coordinate cross-module
   business operations explicitly while preserving shared transactions needed
   for atomic invariants. Avoid a blanket rule that every module must transact
   independently.
3. Split a long workflow into meaningful operations while keeping the business
   sequence visible. A payment workflow might record intent, call a provider,
   reconcile an uncertain result, and record completion. A separate class for
   each assignment adds navigation without improving ownership.
4. Update imports, bindings, factories, policies, routes, event listeners, tests,
   and documented entry points together. Check persisted class names in queued
   payloads, failed jobs, morph types, and cached/serialized data. An old class
   may need a temporary compatibility path or a deployment migration until those
   records are drained or migrated; document its removal condition. Do not drop
   queued work to make a namespace cleanup succeed.
   Update ordinary callers to the canonical namespace and remove obsolete aliases
   or forwarding wrappers once their migration purpose is complete. Preserve one
   active business implementation instead of leaving parallel legacy workflows.
5. Apply one bounded slice and verify its behavior before proceeding. Keep
   unrelated defects separate unless the user authorizes fixing them.

## Completion audit

1. Reconcile every responsibility and artifact with the original request and
   target layout. Inspect residual services, models and UI components for business
   decisions, provider orchestration, reusable queries and presentation-dependent
   errors. Add discovered in-scope responsibilities that the initial map omitted.
2. Inspect the original locations and all callers for legacy ownership, obsolete
   imports, forwarding wrappers and parallel implementations. Moving a service
   unchanged does not resolve its mixed responsibilities. Verify dependency
   direction and explain each deliberate exception.
3. Verify and record provider-call timing relative to persistence and transaction
   boundaries for each affected integration. Attach this evidence to the final
   map alongside canonical classes and callers, retained responsibilities,
   behavior checks and any compatibility transition. Namespace
   and dependency inspection establish placement; tests and static analysis
   support behavior/type checks. Neither evidence category replaces the other.
   Avoid tests that merely assert directory names or class locations.
4. Report complete, partial or unverified against the agreed scope. Remaining
   agreed responsibilities make the refactor partial; unavailable evidence remains
   unverified. A retained owner is an exception only when justified by the agreed
   design, not because moving it would delay completion. List deferred work,
   dependency exceptions and removal conditions for temporary compatibility paths.

For example, registration can be complete while Company is partial: assortment
models still in app/Models/Company, pricing orchestration still in a mixed legacy
service or reusable rate queries still in Livewire remain in-scope ownership work.
The [Company example](layered-context-example.md) illustrates the full map and
preservation guarantees without asserting an actual application has been audited.

## When extraction earns a package

Extract only when requested and when a consumer can use coherent public
operations without reconstructing the internals. Include usable Laravel defaults,
persistence and migrations where appropriate. Use extension points for real
variation, not dozens of mandatory storage/locking/effect interfaces.

Verify extraction in a separate minimal consumer with only declared dependencies.
Workspace tests can accidentally supply undeclared application classes or
dependencies. A Filament companion should call a usable headless API; it should
not supply missing business behavior. Report package independence as unverified
until the separate consumer runs.

## Billing example, only when relevant

Billing can own invoices, payment attempts, mandates, and credits; subscriptions
can own billing periods and cancellation eligibility; orders can own purchase
state; fulfillment can own delivery attempts. Preserve the actual product rules.
Registrar payloads belong to the domain-provider integration, not subscription
rules. Keep uncertain provider outcomes and completion deduplication intact.
This is a responsibility example, not a required folder tree.
