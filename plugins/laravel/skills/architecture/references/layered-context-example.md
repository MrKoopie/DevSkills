# Layered Company context example

Use when designing or refactoring a layered context. This is an illustrative
starting point and a selected target, based on a supplied Company proposal; it
does not establish an actual application's current structure or verified behavior.
Inspect the repository's established contexts and actual responsibilities first.
Apply the user's selected layout or the repository's convention. Create only
components that own a concrete responsibility.

## Starting point and selected target

Suppose Company and CompanyNote already live in Domain/Company/Models, but
assortment records remain in Models/Company. Registration orchestration is in
Domain/Company/Actions; a legacy CompanyAssortmentService combines provider calls,
transactions, pricing rules and queries; Livewire components contain reusable
assortment/rate queries. Moving registration alone leaves the module refactor
partial when all these capabilities are in the agreed scope.

The selected target groups Company controllers and Livewire with its Application
operations, Company records and rules in Domain, and providers in Infrastructure:

```text
app/
├── Application/Company/
│   ├── Actions/
│   │   ├── RegisterCompany.php
│   │   ├── UpdateCompanyProfile.php
│   │   ├── CreateAssortmentArticle.php
│   │   ├── SetArticleAvailability.php
│   │   ├── SupersedeArticlePrice.php
│   │   ├── ChangeArticlePriceValidity.php
│   │   ├── WithdrawArticlePrice.php
│   │   ├── RestoreAssortmentArticle.php
│   │   ├── RestoreArticlePrice.php
│   │   └── ReconcileArticleAvailability.php
│   ├── Controllers/
│   │   ├── CompanyController.php
│   │   └── CompanyArticleController.php
│   └── Livewire/
│       ├── CompanyOverview.php
│       ├── CompanyDetailsTabs.php
│       ├── CompanyNotes.php
│       ├── CompanyAssortment.php
│       └── CompanyArticlePrices.php
├── Domain/Company/
│   ├── Models/
│   │   ├── Company.php
│   │   ├── CompanyNote.php
│   │   ├── CompanyAssortmentSet.php
│   │   ├── CompanyArticle.php
│   │   └── CompanyArticleRate.php
│   ├── Services/
│   │   ├── ArticlePriceTimeline.php
│   │   └── ArticleAvailabilityPolicy.php
│   ├── Queries/
│   │   ├── CompanyAssortmentQuery.php
│   │   └── CompanyArticleRatesQuery.php
│   ├── ValueObjects/
│   │   ├── VatNumber.php
│   │   └── PricePeriod.php
│   ├── Contracts/
│   │   ├── CompanyProductCatalog.php
│   │   └── VatNumberVerifier.php
│   ├── Enums/
│   │   ├── InvoicingMethod.php
│   │   └── VatVerificationStatus.php
│   └── Exceptions/
│       ├── CompanyVatVerificationFailed.php
│       ├── ArticleMappingConflict.php
│       ├── ArticlePriceConflict.php
│       └── ArticlePriceChangeRejected.php
├── Infrastructure/Company/Integrations/
│   ├── Spectrum/SpectrumCompanyProductCatalog.php
│   └── Vies/ViesCompanyVatNumberVerifier.php
├── Http/Requests/Company/
│   ├── StoreCompanyRequest.php
│   └── UpdateCompanyRequest.php
├── Policies/Company/
│   ├── CompanyPolicy.php
│   └── CompanyNotePolicy.php
└── Console/Commands/
    └── DeactivateExpiredCompanyArticles.php
```

Views, routes, configuration, migrations and factories also retain their normal
Laravel locations. Update their class references when namespaces change. The
existing Spectrum client and VIES validator remain reusable infrastructure;
Company adapters expose its business needs and neutral outcomes rather than
duplicating those clients.

## Full responsibility map

Paths below are relative to app/. This is a planning map: every proposed move is
planned, evidence is pending and no implementation is claimed complete. During
the actual refactor, add verification evidence and a final status per row using
the [refactoring map](refactoring.md#scope-and-placement). Confirm each starting
owner from source; the supplied example does not replace that investigation.

| Capability/artifact | Illustrative starting owner | Selected owner/path | Decision and reason |
| --- | --- | --- | --- |
| Company and note records | Domain/Company/Models | Same owner/path | Retain: entity state, relationships and local rules already have an owner. |
| Assortment set, article and rate records | Models/Company | Domain/Company/Models | Move all three: Company owns these records under the selected layout. |
| Registration and profile updates | Domain/Company/Actions | Application/Company/Actions/RegisterCompany and UpdateCompanyProfile | Move orchestration: provider calls, related records and transaction sequencing are Application responsibilities. |
| VAT value and remote verification | Domain/Company/ValueObjects/VatNumber; Services/Vat/ViesVatNumberValidator called by registration | Domain/Company/ValueObjects and Contracts/VatNumberVerifier; Infrastructure/Company/Integrations/Vies | Retain intrinsic validation; adapt remote verification: neutral outcomes protect the business/provider boundary. |
| Notes create/delete | Livewire/Company/CompanyNotes | Application/Company/Livewire/CompanyNotes; Domain/Company/Models/CompanyNote | Move entry point; retain direct CRUD with company scoping, authorization and validation. |
| Create assortment article and initial rate | Services/Company/CompanyAssortmentService | Application/Company/Actions/CreateAssortmentArticle | Extract coordinated creation and mapping serialization. |
| Change article availability | Assortment service and its UI callers | Application/Company/Actions/SetArticleAvailability; Domain/Company/Services/ArticleAvailabilityPolicy | Separate persistence orchestration from the business decision. |
| Supersede price, adjust predecessor, change validity | CompanyAssortmentService | Application/Company/Actions/SupersedeArticlePrice and ChangeArticlePriceValidity | Extract atomic rate workflows while preserving lock ordering. |
| Price overlap, timeline and period rules | CompanyAssortmentService | Domain/Company/Services/ArticlePriceTimeline; ValueObjects/PricePeriod; owning model predicates | Extract cross-rate rules; retain entity-local behavior on models. |
| Withdraw/restore a rate and reconcile availability | CompanyAssortmentService | Application/Company/Actions/WithdrawArticlePrice and RestoreArticlePrice | Extract coordinated writes and availability reconciliation. |
| Restore article and reject mapping conflicts | CompanyAssortmentService | Application/Company/Actions/RestoreAssortmentArticle | Extract restoration while preserving company-level mapping serialization. |
| Expiry/reactivation decision and persistence | Domain/Company/Actions/ReconcileArticleAvailability; expiry command; assortment service | Domain/Company/Services/ArticleAvailabilityPolicy; Application/Company/Actions/ReconcileArticleAvailability | Move workflow; isolate rules; retain the command's conventional location. |
| Assortment filtering and rate retrieval | Livewire/Company/CompanyAssortment and CompanyArticlePrices; assortment service | Domain/Company/Queries/CompanyAssortmentQuery and CompanyArticleRatesQuery, or sufficient existing scopes/builders | Extract reusable semantics; keep UI pagination state at the entry point. |
| Spectrum search, mapping and reference prices | CompanyAssortmentService and existing Spectrum client | Domain/Company/Contracts/CompanyProductCatalog; Infrastructure/Company/Integrations/Spectrum | Adapt the existing client to the Company's needs and neutral outcomes. |
| Controllers, Livewire and form-error translation | Http/Controllers/Company; Livewire/Company; business service/action errors | Application/Company/Controllers and Livewire | Move adapters as selected; translate neutral failures at the presentation edge. |
| Requests, actor authorization and supporting framework files | Http/Requests, Policies, Console/Commands, views/routes/configuration/migrations/factories | Same framework locations, updated references | Retain by design: the module's selected layout explicitly keeps these locations. |

Use an agreed exception when a capability genuinely remains owned elsewhere.
Do not label leftover Company records as shared merely to avoid migrating them.
If pricing is deferred without an agreed scope reduction, Company remains partial.

## Trace representative workflows

1. **Register company:** the controller authorizes, validates and maps input.
   RegisterCompany coordinates VatNumberVerifier and Company persistence using
   the existing provider-call timing and transaction guarantees. VatNumber owns
   intrinsic value validation; it does not establish remote VAT registration.
   ViesCompanyVatNumberVerifier implements the contract by reusing the existing
   validator and translating provider responses into verified, rejected or
   unavailable outcomes. The controller/Livewire component translates neutral
   failures into form errors. Domain imports neither the concrete client nor UI.
2. **Supersede article price:** the Application action acquires the required locks,
   loads the article/rates, invokes timeline/period rules and coordinates the
   predecessor adjustment, new rate and availability reconciliation atomically.
   ArticlePriceTimeline earns a service for rules spanning rates; predicates and
   mutations concerning one entity remain on its model. Domain rejects invalid
   changes neutrally; the entry point presents the error.
3. **Reconcile availability:** the conventional expiry command invokes the
   Application action. That action acquires locks, asks ArticleAvailabilityPolicy
   for the business decision and persists it. This service decides eligibility
   for expiry/reactivation; Policies/Company contains actor authorization instead.

An established context comparison should likewise name its real entry point,
Application operation, Domain rule/model, persistence path and integration
contract/adapter. Identify dependency weaknesses instead of copying every detail.

## Keep simple work direct

1. Rename an article through validated, authorized CRUD while retaining existing
   transaction/locking behavior. Relocation does not require a wrapper action.
2. Create/delete notes directly with company scoping and authorization. Preserve
   model invariants across every caller.
3. Soft-delete an article through its guarded model operation and authorized entry
   point, retaining lock behavior; an action solely forwarding delete() adds no
   responsibility.
4. Reuse sufficient typed scopes/builders for queries. The illustrated Queries
   directory earns classes only for cohesive retrieval responsibilities beyond
   those helpers. UI pagination state and presentation remain with the adapter.
5. Use focused availability rules here. Determine whether actual transition rules
   justify a state machine; adopting another context's layout alone does not.

## Preservation and completion evidence

The supplied Company proposal requires article/rate pricing changes to remain
atomic, company-level mapping serialization during creation/restoration, and
article-first locking for price operations. Confirm the actual application's
implementation and preserve these guarantees through extraction. Other domains
need their own invariants and lock order, not this example's specific scheme.

Check updated relations, factories, policies, bindings, routes, UI registration,
commands and tests, plus persisted class references and compatibility transitions.
Verify behavior/concurrency with appropriate application checks. Inspect residual
service/UI code and canonical namespaces separately for ownership completeness.
Do not infer either runtime behavior or architectural completion from this tree.

For a concrete partial result, registration may be migrated and its checks pass,
while CompanyArticle remains in Models/Company and CompanyArticlePrices still
owns reusable rate rules. Report registration complete within its verified slice
and the module refactor partial, with those responsibilities and evidence gaps
listed. A narrow completed map does not override the original full-module scope.
