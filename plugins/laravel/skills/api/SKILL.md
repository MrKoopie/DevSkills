---
name: api
description: Use when adding or reviewing Laravel API endpoints, request and response contracts, API versioning, client compatibility, deprecation, or API documentation.
---

# Laravel API contracts

Start with [project context](../../references/project-context.md). Read existing
routes, requests, resources, client contracts, and API tests. Preserve the API's
established authentication, response envelope and versioning strategy.

1. Identify the request, successful response, validation failure, authorization
   boundary, and side effects. Scope retrieval and related IDs to the authorized
   tenant. Token abilities complement resource policies; authentication alone is
   not resource authorization.
2. Keep transport details in requests/controllers/resources and business
   invariants in the owning operation. Share business behavior across API, UI,
   CLI and jobs. Introduce transport-to-domain DTO mapping only when the boundary
   meaningfully differs; ordinary endpoints do not require two DTO layers.
3. Classify compatibility before changing an existing endpoint. A changed field
   name/type, newly required input, error/status behavior, ordering, pagination,
   permission rule or enum case can break clients. An additive field is compatible
   only with clients that tolerate it. Do not create a new API version merely for
   a new endpoint or automatically impose URL versioning on an existing API.
4. When versions differ, isolate the differing request/response mappings and
   preserve the contracted semantics of older clients. Domain behavior is shared
   where its contract matches; a public behavioral difference may need an explicit
   policy/operation difference rather than a cosmetic resource transformation.
5. Apply bounded pagination, allowlisted filters/sorts/includes, suitable rate
   limits, and explicit serialization. Avoid exposing model attributes or
   relationships accidentally. Use the project's existing documentation tool;
   installing Scribe or another generator is not a prerequisite.
6. For retirement, read [deprecation](references/deprecation.md). For new domain
   behavior, read the sibling [implement skill](../implement/SKILL.md). Use
   [testing](../testing/SKILL.md) for contract tests, then the shared
   [verification procedure](../../references/verification.md).

Review contract changes against actual consumers and tests, not only schema shape.
Include valid, invalid, guest, forbidden and cross-tenant cases as relevant, and
verify denied requests produce no forbidden side effect. In review-only mode,
report findings without modifying endpoints.
