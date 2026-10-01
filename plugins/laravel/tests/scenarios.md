# Skill value and routing scenarios

Use these prompts against the packaged skills and minimal matching project
fixtures. Evaluate the resulting decisions/code, not whether wording is repeated.
For routing, expose only skill names/descriptions before selection; for execution,
make the selected skill and references available. A manual walkthrough can identify
conflicts but does not prove model selection or application runtime behavior.

For each run record the fixture/version, selected skills, actual output/artifact,
observations against the criteria, and limitations. Mark a case pass only for the
evidence level actually exercised. Store generated reports outside the package.

| ID | Realistic request and fixture | Primary skill | Evidence of useful behavior |
| --- | --- | --- | --- |
| A1 | Design a small inventory CRUD feature in a conventional Laravel app; no shared orchestration or package requirement. | architecture | Preserves conventions, explains ownership, avoids a mandatory DDD tree/repositories/DTOs, and makes no implementation changes for a design request. |
| A2 | Move an invoicing operation to another module; queued payloads still contain the old class name. | architecture | Inventories callers and persisted references, preserves business invariants, and proposes a safe transition for queued work rather than deleting it. |
| A3 | Extract a billing package that must be reusable in another app. | architecture | Defines a usable boundary and separate consumer verification; does not claim independence from workspace-only tests. |
| A4 | Sales and Billing both have a Customer class but disagree about its lifecycle and required fields. | architecture | Considers bounded contexts and explicit contracts; does not force a shared model/DTO merely to remove similar code. |
| A5 | Add a DateRange value object and typed input DTO to an existing DDD operation. | architecture, then implement | Preserves local action/DI conventions, construction invariants, immutable value operations, and validation at each untrusted input boundary. |
| I1 | Simplify a status filter where null means all, 0 means pending and 1 means complete. | implement | Keeps filtering for 0; if using when with a boolean condition, captures the actual status in the callback. |
| I2 | Replace a loop that updates a found value for every matching candidate. Existing behavior returns the last match. | implement | Preserves last-match semantics or identifies the intended behavior change before using first(). |
| I3 | A state transition checks its guard before save. Remove its database lock to shorten the code. | implement | Examines the concurrent invariant and package/database behavior; does not equate a guard check with atomicity. |
| I4 | A payment job times out after the provider may have charged. Retry it; the SDK already has tests. | implement | Uses native job failure handling, preserves operation identity and reconciliation, and still tests the application's adapter and duplicate behavior. |
| I5 | Review a changed query for security problems; do not edit files. | implement | Traces input, tenant scope and callers; returns actionable evidence only and makes no edits. |
| I6 | Add a second helpdesk import provider with overlapping external IDs, regional locales and nested categories. | implement | Keeps provider mapping behind a capability boundary, enforces source-aware uniqueness, retains full locale identity and handles parent dependencies without a transaction around remote pagination. |
| T1 | Add regression coverage to a PHPUnit app with existing criteria and an isolated MySQL database. | testing | Uses PHPUnit and existing bindings, does not re-ask answered questions, asserts the violated behavior and a relevant negative case. |
| T2 | Add a guest API test beside tests sharing actingAs setup. | testing | Ensures the request is genuinely unauthenticated; does not invent withoutAuth(). |
| T3 | Queue::fake passes and SQLite tests pass. Can we claim the MySQL concurrent job is verified? | testing | Separates dispatch, execution and database-engine evidence; identifies what remains unverified. |
| P1 | Add an optional field and new enum case to an API consumed by a strict generated client. | api | Checks consumer compatibility instead of calling all additive changes non-breaking. |
| P2 | Deprecate v1, with agreed dates and existing Link headers; prepare the change but do not notify clients. | api | Uses structured-date Deprecation and HTTP-date Sunset, preserves other links, and sends no communications. |
| P3 | A user can POST another tenant's category_id to an authenticated endpoint. | api | Validates membership/relationship scope and resource policy; denied request leaves no forbidden effect. |
| F1 | Build a category Select in Filament 5; forged related IDs must be rejected. | filament | Checks installed APIs and actual scope, configures relationship query/validation correctly, and tests forged submissions. |
| F2 | Change a translated label on a panel registered outside app/Filament. | filament | Follows the existing layout, makes the small localized change, and avoids architecture redesign or unnecessary tests. |
| F3 | Upgrade a Filament panel to the explicitly requested major; one plugin is incompatible. | filament | Checks target compatibility and reports the concrete blocker without silently choosing a newer major. |
| F4 | A bulk action queues exports and shows Completed immediately; review its UX. | filament | Distinguishes queued from completed, checks per-record access/output scope, and does not infer successful execution from a screenshot. |
| N1 | Explain a generic PHP foreach loop in a standalone script. | none | Does not load Laravel workflows solely because PHP is mentioned. |
| N2 | Rename a Laravel success-label translation key in a conventional Livewire editor with an app/Models model and existing authorized, validated transaction/lock behavior. | implement | Changes the relevant label only, preserves model/entry-point placement and guarded persistence, and creates no new actions, contracts or query classes. Does not load all five skills or insist on new architecture. |

## Benchmark follow-up scenarios

| ID | Realistic request and fixture | Primary skill | Evidence of useful behavior |
| --- | --- | --- | --- |
| A6 | Design a helpdesk with email and WhatsApp import, a customer portal and crew panel; people contact support before registering and retain history after login removal. List files only. | architecture | Separates customer/contact lifecycle from login, explains account linking, shows both channel paths, distinguishes plain model writes from workflows needing actions, and avoids mandatory DTOs/builders. Makes no application files. |
| I7 | A signed chat webhook arrives from an unlinked sender with a supplied customer ID and two possible open tickets; a retry follows a crash after receipt persistence. | implement | Does not treat provider authenticity as account ownership or choose an arbitrary conversation; defines unresolved matching behavior, source uniqueness, idempotent processing and recovery of recorded but undispatched receipts. |
| A7 | Propose a layered DDD file structure for incoming email and WhatsApp messages that become helpdesk tickets. Another developer must understand the directory tree without the discussion history. | architecture | Shows explicit Email and WhatsApp/Twilio boundaries under the selected context-first or channel-first layout, with shared orchestration in Application and business rules in Domain. Shows both entry points, where they converge, and source identity on shared records. Explains imported versus ticket messages without duplicating common workflows or hiding channels under a generic intake bucket. |
| A8 | Design a module-wide Company refactor covering registration, VAT, notes, assortment, pricing, restoration, availability and queries. The supplied established Purchasing workflow has an entry point, application action, domain rules/models, persistence and a provider adapter; one rule directly imports a concrete provider client. The user selects Application/Company controllers/Livewire, Domain/Company models and Infrastructure/Company/Integrations providers. | architecture | Traces the complete existing workflow with actual classes, identifies conventions and the dependency weakness, and maps all capabilities/current artifacts to target owners/paths. Applies the selected placement, records intentional retained framework paths and avoids copying unrelated state-machine machinery. |
| A9 | Assess the same Company refactor for completion. A teammate marks a registration-only map complete and reports green tests/PHPStan; assortment models remain in app/Models, pricing/restoration live in a mixed service and queries remain in Livewire. Release review is imminent and the teammate calls pricing future cleanup, without user agreement to reduce scope. | architecture | Reconciles the original request, map and residual code; detects omitted responsibilities and remaining legacy placement/dependencies. Reports Company partial, records evidence/final status and preserves concurrency guarantees. Does not treat tests, a narrow map or an unapproved deferral as full architectural completion. |
| A10 | Design a Company VAT workflow with one VIES provider and an existing validator, neutral verified/rejected/unavailable outcomes, a sufficient Eloquent rate scope, guarded note CRUD and a separate availability business rule. | architecture | Justifies the outbound business contract without inventing providers, reuses the validator through an Infrastructure adapter, keeps workflow orchestration in Application and form errors at the entry point. Retains sufficient scopes and guarded CRUD; distinguishes intrinsic VAT validation, remote verification, availability rules and actor authorization. |
| F5 | Design a layered DDD Filament knowledge base editor. Creating/editing saves validated article fields. Publishing additionally checks approval and queues a search-index update after commit. Filament is the sole current caller. | architecture, filament | Keeps plain create/update on native CRUD and assigns publication orchestration to an Application action invoking Domain rules. Preserves policies and validation. Explains the action's responsibility beyond persistence; adds no unrequested business rules or wrapper actions. |
| F6 | Wire existing article actions into Filament create/edit pages and a modal editor. An afterSave callback currently calls the update action after the normal save. | filament | Uses version-appropriate persistence replacement on the actual owning page/UI action, avoiding a second write. Checks related writes, authorization and rejection before persistence. |
| F7 | Add an article editor in DDD Filament where create/update only save form fields and publication only updates a boolean, with ordinary validation and policies. | architecture, filament | Creates no wrapper actions for bare model create/update, including no action justified only by the name PublishArticle. Keeps permission checks and native persistence; does not invent additional effects. |

## Value acceptance criteria

1. Each skill owns a distinct user outcome; a sibling is loaded only when its
   responsibility is actually needed.
2. Shared preparation reuses already established facts and asks only unresolved
   consequential questions.
3. Every instruction changes a relevant decision, preserves an invariant, enables
   verification, or prevents a demonstrated failure. Remove redundant guidance.
4. No scenario requires an agent, a particular model, an unavailable personal
   skill, or an unrequested dependency/architecture migration.
5. Completion claims match the evidence: package checks, manual walkthrough,
   model execution, application tests, browser checks, and provider proof are
   distinct results.
