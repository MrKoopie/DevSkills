# Domain modeling and component contracts

Use when designing, implementing, or reviewing domain components. Apply the
project's established DDD conventions when it has them. These rules describe
responsibilities; they do not require creating every component for every feature.

## Business boundaries and vocabulary

1. Name business domains and integration feature folders by the capability or
   records they own, such as Billing, Email or WhatsApp. A direction or
   mechanism alone, such as Inbound, Sync or Processing, does not say what the
   feature handles. Class names also identify the object and effect:
   ImportMailboxEmails or AttachImportedMessageToTicket communicates more
   than RecordInboundReceipt or ResolveInboundReceipt. Standard structural folders
   such as Models, Actions, App and Integrations remain useful. For existing code,
   keep renaming within the requested scope and preserve persisted class references.
   For multiple channels, show channel/provider-specific entry points and mappings
   explicitly, then identify any shared operation and stored source discriminator.
   Renaming a generic intake folder does not by itself explain email versus WhatsApp.
2. Keep the business vocabulary consistent across code, tests and documentation.
   Where the same word has different rules or meanings, consider bounded contexts:
   a Sales customer and a Billing account need not share one model just because
   both represent a person or company. Team ownership can reinforce a boundary;
   team size alone is not a reason to split the application.
3. Within an established context boundary, keep internal models and writes owned
   by that context. Communicate through explicit public operations/contracts or
   published events instead of importing another context's internal implementation.
   Use a synchronous operation when the caller needs a result or shared atomicity;
   use an event for a fact and reactions that can honor the chosen delivery timing.
   Do not replace an atomic invariant with eventual consistency as a style cleanup.
4. Share a small kernel only when the concept has the same semantics and agreed
   ownership in every consumer. Similar field shapes alone do not justify a shared
   Customer DTO or a growing Common module. DRY applies to the same business rule,
   not coincidentally similar code in different contexts.
5. Keep feature/domain grouping when organizing Actions, Data/DTO, Models, Enums,
   QueryBuilders, ValueObjects, Events, Listeners, Exceptions and Contracts. Create
   only the roles that exist and follow local namespace conventions. Eloquent
   models can serve as domain entities without a duplicate entity layer.

## Choosing boundaries without adding layers

Separate authentication identity from business identity when their lifecycles
differ. A customer/contact may exist before a login, retain history after login
access is removed, or have multiple verified channel addresses. In those cases,
model the customer/contact independently and define how an account gains access.
A User model alone can be sufficient when those lifecycles truly coincide; do not
create a separate Customer model solely to complete a directory template.

In an existing or selected layered design, workflow orchestration belongs in
Application; business records, values, rules and entity behavior belong in Domain.
Infrastructure implements provider contracts. Domain rules do not depend on UI,
Application operations or concrete provider adapters. Eloquent can remain the
domain entity/persistence representation under this Laravel design. Entry points
validate, authorize, invoke workflows and translate outcomes; their namespaces
follow the agreed layout. The [Company example](layered-context-example.md) places
controllers and Livewire under Application while retaining conventional requests,
authorization policies and commands.

Organize integrations by meaningful context, channel and provider ownership.
For example, Infrastructure/Company/Integrations/Vies is context-first;
Infrastructure/Integrations/WhatsApp/Twilio is channel-first. Follow the selected
layout and expose each channel/provider's flow explicitly. Provider clients,
payload mapping and transport adapters live at that integration boundary.

Inbound adapters map external input and invoke Application operations rather than
writing another context's tables. Outbound Application workflows invoke neutral
contracts owned by the consuming business boundary; Infrastructure adapters
implement them and map provider outcomes. A single provider can justify a contract
when it protects that boundary; ordinary internal services need no automatic
interface. Preserve provider-call timing, transaction ownership and failure
semantics while moving code.

Share common behavior at its owning layer, without merging channel-specific code
into a generic Inbound or SupportMessageImport integration bucket. Separate Email
and WhatsApp folders do not require separate ticket models, duplicate workflows
or separate databases.
Preserve existing layouts during unrelated edits and make any layer migration
an explicit part of the requested scope.

Do not create an action if it is just a model update or create. Saving validated
article fields with ordinary policy checks can use native CRUD, including in DDD
and Filament. A class that only forwards to create(), update() or save() adds no
business operation. Model invariants still apply on every mutation path.

Use an action when it coordinates a business workflow: for example, checking
publication eligibility, changing article state and scheduling a publication effect
after commit. Filament calls that operation even if it is the only caller. A name
such as PublishArticle does not justify an action when the entire behavior is a
plain field update. Explain the responsibility beyond persistence instead of
inventing rules or effects to justify a class. Read/list work can use queries or
scopes. DTOs, custom builders and value objects each need an actual contract.
Preserve existing behavior and scope when applying these distinctions to old code.

## Component contracts

| Component | Contract to preserve |
| --- | --- |
| Action | One cohesive business operation with explicit typed inputs/results and a responsibility beyond a bare model create/update. In layered designs, Application actions coordinate workflows and invoke Domain rules. Prefer composition and constructor injection for collaborators. In projects using the original convention, use a final class and a single public execute method; respect an established alternative such as an invokable action. Compose operations while keeping transaction ownership and side-effect ordering visible. |
| DTO | An explicit data contract at a meaningful boundary. Prefer typed, immutable properties and typed nested values over an opaque array of mixed fields for complex action inputs. Map external/form data at the boundary; ordinary scalar parameters and known framework arrays need not become DTOs. Use the installed DTO library or a plain PHP type without adding a package solely for the pattern. |
| Model | Own entity-specific calculations, valid-state predicates and mutations. Keep rich behavior near the state it governs; actions coordinate multi-entity workflows. Do not move all behavior into services, or put HTTP/UI concerns and provider orchestration into models. Enforce invalid-state rejection on the mutation path, not only in a can-method used by the UI. |
| Query scope/builder | Encapsulate reusable query semantics and return a chainable, accurately typed builder. Follow installed Laravel registration conventions and static-analysis types. Do not use query helpers as a substitute for mutation invariants or resource authorization. |
| Value object | Represent a domain value by its content rather than database identity. Validate invariants at construction, compare by value, and return new instances for changes. Prefer final immutable types, with readonly support appropriate to the project's PHP version. Named factories must preserve the same invariants as direct construction. |
| Enum | Express a genuinely closed vocabulary with stable backed values when persisted or exposed. Preserve integer/string storage contracts; keep domain predicates close to the enum. Presentation labels/colors follow the application's existing UI boundary and must not introduce host-specific translation dependencies into a reusable domain package. |
| Event/listener | Name a completed business fact in the past tense, such as OrderPlaced. Keep the event a meaningful data carrier and delegate a listener's business work to its owning operation. Register/discover listeners using the installed application's convention. Preserve after-commit timing, retry and deduplication semantics; an event is not an automatic reliability boundary. |
| Entry point | Controllers, CLI commands, Livewire and Filament adapters authorize and validate input, invoke owning workflow actions, and translate results. Namespace placement follows the selected layout. Plain model create/update can use native CRUD without a wrapper action. Filament UI Actions configure interaction; Application actions own workflow orchestration in layered designs. Keep model invariants enforced across callers. API Resources own explicit response serialization. |
| Exception/result | Express a meaningful domain rejection with a typed exception or outcome consistent with the project. Translate it into the correct user/API response at the edge; avoid strings that callers must parse or success-shaped fallbacks that hide failures. |

## Validity is separate from representation

A typed DTO or validation attribute does not by itself prove every construction
path validates input. Check request, CLI, job and named-factory paths. Keep
intrinsic value invariants in the value object; keep actor permissions and mutable
database conditions in the appropriate policy/operation. Readonly properties do
not make referenced mutable objects deeply immutable.

Keep consumer-extensible identifiers, such as arbitrary fulfillment subject types,
open rather than encoding them as a closed enum. A result carrying both a fixed
outcome and data can use a DTO with an enum field; an unused option should be
removed rather than wrapped in another type.

For Money, define precision, currency matching and the business rules for negative
amounts and rounding. Do not copy a float-based cents conversion or assume every
currency has two decimals. For DateRange, reject an end before its start. Tests
should exercise these rules and non-mutating operations, not simply construction
of a data holder.

Use recognizable names within local conventions: verb/noun actions (CreateOrder),
specific input/result DTOs (CreateOrderData, ConnectionTestResult), singular model
names (Order), domain value names (Money), and past-tense facts (OrderPlaced).
Avoid introducing a base class, repository, interface or abstract factory without
a concrete shared contract. Small stateless calculators can remain focused
services; every calculation does not need its own workflow action.
