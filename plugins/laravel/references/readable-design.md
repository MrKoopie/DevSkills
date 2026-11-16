# Readable design: shared decision rules

Architecture, implementation and review must apply these rules to the affected
flow. Read them once per task and reuse the decisions. These are agreed working
rules, including proposals awaiting broader application evidence; they are not
claims that every existing project or pilot already satisfies them. Record only
material choices: problem, smallest useful change, reason, preserved behavior and
remaining uncertainty. Do not create a report for every internal edit.

## Choose boundaries that reduce the whole flow's complexity

- Start with the installed framework's native models, relationships, validation,
  policies and queries. Use scopes for genuinely recurring selection semantics.
  A separate query class is optional, useful when a cohesive complex selection
  becomes easier to follow. A repository needs a concrete storage boundary or
  shared storage complexity; wrapping Eloquent or hypothetical future replacement
  is insufficient. DDD, SOLID and DRY are reasoning tools, not file quotas.
- For **every refactor**, consult the architecture skill before editing, including
  small extractions and migration to a component. Scale the check to the change:
  for a tiny edit, inspect affected responsibility, caller and invariant and state
  briefly whether ownership should stay. A large map or redesign is unnecessary.
  Evaluate Livewire, Filament or React/Inertia on its own lifecycle and installed
  conventions; a Livewire solution is not a universal component rule.
- Keep one-use, straightforward behavior near its caller, with a few meaningful
  local methods if needed. An action needs actual reuse or a cohesive responsibility
  whose isolation improves understanding: for example one atomic issuance, price
  calculation or document operation. One caller does not prohibit that boundary;
  multiple callers do not justify an empty wrapper. Remove pass-through layers
  when they add no invariant, policy or understandable operation. Do not replace
  one context query with a context action merely to satisfy a naming rule.
- Pass the minimum already available facts from caller to component. Avoid making
  a reusable component depend on a legacy lookup just to rediscover those facts.
  Inspect one step upstream when that gives a simpler contract; broaden only for
  a demonstrated in-scope dependency, not an application-wide cleanup. Client
  state remains untrusted: authorize identities server-side and reread mutable
  state where freshness or concurrency requires it. Reuse existing capability or
  identity checks before adding detection logic. Distinguish an empty result from
  an unsupported feature or unavailable provider; do not infer support from an
  incidental customer-number format.

## Match protection and recovery to agreed needs

Choose the simplest solution that supports agreed correctness and operations.
Before adding locks, transactions, idempotency, retries, periodic checks or recovery
mechanisms, inspect the guarantees the framework and existing application already
provide. Add protection only when a concrete requirement or demonstrable risk makes
it necessary; a technically describable failure alone does not establish that need.

Distinguish three decisions: describing how a failure could occur, showing why
existing guarantees are insufficient, and establishing that recovery must happen
automatically. Automatic recovery is an explicit functional choice, not an implied
consequence of finding a possible failure. When existing error handling and an
authorized manual recovery action meet agreed operations, use them. Do not add
periodic scans, age thresholds, redispatch or status transitions without that need.

Architecture, implementation and review use these same questions:

- Which concrete requirement does this mechanism protect?
- Which existing guarantees are insufficient?
- What correctness or agreed service would be lost if it disappeared?
- Would existing error handling plus a manual recovery action suffice?

Preserve protection demonstrably needed for atomic writes, concurrent updates or
duplicate external effects. Remove existing protection only after verifying that
its guarantee is unnecessary or preserved another way. Manual retry must also be
safe: a queue does not make uncertain email acceptance safe to retry. Establish
the external outcome or use supported deduplication before repeating the effect;
otherwise retain the uncertainty and require an informed resolution.

For example, in the supplied GoldenEye quotation case, generation/email jobs
already had attempts, backoff and failure callbacks, with manual regenerate/send
actions. A commit-to-enqueue gap motivated an additional scheduled reconciler,
but automatic recovery was not agreed. The user chose native queue handling and
manual retry, so the command and schedule were removed while the jobs, manual
actions and necessary correctness checks remained. This illustrates an operational
choice, not a ban on reconciliation: an explicit automatic-recovery requirement
or demonstrated unmet guarantee can justify additional protection in another flow.

## Query boundary is strict

A query file/class only selects and reads. Filters, joins, ordering, pagination,
loading relationships and direct selected-field projections belong here. Applying
an already authorized tenant constraint is selection, not a permission decision.
Queries do not decide actor access, interpret provider payloads, resolve customer
identity, select business outcomes, build form/document context, coordinate
workflows or perform writes. Trace collaborators and model hooks too: an indirect
link creation is still a write. A read-looking name does not establish purity.

When a query violates this boundary, remove redundant preparation first. Keep
plain selections inline or in existing scopes where readable; put necessary
policy decisions, integration interpretation and mutations with their existing
owners. Only introduce a new class if the whole caller-to-result flow benefits.

## Follow data and behavior through the lifecycle

- Trace initialization, render, updates, preview, save, failure and refresh as
  applicable. Reuse prepared data instead of reconstructing the same context after
  preview/save. Do not cache away required fresh permission or locked-state reads.
- Normalize input once at its true boundary and name its meaning. Distinguish
  absent, null, empty, false, zero and invalid where the contract does. Repeated
  empty checks may reveal a vague input contract; fix that cause before adding a
  helper. Prefer readable rejection guards and separate meaningful steps to long
  mixed conditions, preserving short-circuiting, side effects and error priority.
- A DTO must convey a coherent, actually consumed contract. Do not use one
  half-populated type for incompatible list/detail meanings. Give different
  meanings an explicit representation when needed; do not automatically create
  a new DTO for every projection or three ordinary scalars. Remove unused fields
  only after checking all consumers and serialization contracts.
- A transaction should make the steps that must succeed together apparent. Move
  independent preparation outside only when snapshot, locking and atomicity allow
  it. Keep a coherent operation and a few meaningful local steps; do not hide it
  in dozens of wrappers. Prefer the existing callback when clear. Manual
  begin/commit/rollback is allowed only with a concrete readability/control benefit
  and equivalent rollback, exception, retry, nesting/savepoint and after-commit
  behavior. An early return or caught exception must not silently commit a failed
  operation. External effects require explicit timing and failure semantics.
- Read top-to-bottom: use meaningful names, consistent indentation and blank lines
  to group cohesive steps and separate changes of responsibility. Wrap long
  chains, conditions, callbacks, argument lists and payloads at meaningful
  boundaries, using roughly 120 characters as a readability guideline rather
  than a hard limit. Preserve evaluation order, short-circuiting and behavior;
  add no helpers, classes or control-flow changes solely to achieve formatting.
  After running the formatter, inspect the result yourself for readable grouping
  and line breaks: formatter success does not establish semantic readability.
  A shorter file or fewer files is not itself success.
  Use the [formatting pilot](formatting.md) for machine-enforceable proposals;
  semantic grouping and the full flow still need human/agent review.

For implementation completion and review, apply the relevant
[review questions](review-questions.md) with the [verification procedure](verification.md).
Questions guide investigation; a finding needs evidence, not a checked box.
