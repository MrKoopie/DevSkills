# Data, authorization, and concurrent writes

## Ownership and access

1. Derive tenant context from an authenticated, authorized selection or explicit
   trusted job/CLI context. Validate membership. Do not accept a posted tenant ID
   as authority. Scope record lookup, relationship assignment, validation, cache
   keys, exports, files, and background work to the correct tenant.
2. Apply policies at each relevant entry point. A hidden button, token ability,
   or successful authentication does not establish resource authorization. Scope
   route bindings and nested relationships consistently with the API's intended
   forbidden/not-found behavior.
3. Use validated input with explicit mass-assignment boundaries. Treat nested
   relationship IDs and sort/include parameters as inputs to validate or allowlist.
   Query bindings protect values, not arbitrary column names or SQL fragments.
4. Inspect the application's tenancy implementation before adding global scopes.
   Avoid per-request static scope registration capturing a tenant ID; long-lived
   workers and alternate entry points need explicit initialization and cleanup.
   Test consecutive operations for different tenants in the same process where
   the application uses persistent workers.

## Transactions and schema

1. Enforce uniqueness and integrity in the database where possible. Use a
   transaction plus appropriate locking or a conditional atomic update for
   concurrent state changes. Inspect related-row invariants and lock ordering;
   a single-row lock does not automatically protect all related writes.
2. Preserve decimal precision or the application's currency/minor-unit model.
   Do not use binary floats for exact monetary calculations or assume every
   currency has two decimals. Fix rounding at a documented business boundary.
3. Separate slow provider calls from database locks where the workflow permits.
   Record durable intent and reconcile uncertain external outcomes. A local
   rollback cannot undo a remote charge.
4. For schema changes, inspect database engine/version and table size. Account for
   indexes, existing invalid rows, migration locks, old/new application versions,
   and resumable backfills. A rollback that drops populated columns is not data
   recovery. Use the project's verified isolated test database for test writes.
5. For performance work, measure the relevant query path. Check N+1 queries,
   selected columns, indexes, pagination and query plans before adding caches.
   If processing mutates the rows being paged, use stable key-based iteration.
   Define cache invalidation and tenant identity, including permission-dependent
   results, before caching a response.

Evidence should cover cross-tenant denial and the actual database semantics used
by an invariant. SQLite-only tests do not prove MySQL/PostgreSQL locking behavior.

Sources: [Laravel queries](https://laravel.com/docs/13.x/queries),
[authorization](https://laravel.com/docs/13.x/authorization), and
[migrations](https://laravel.com/docs/13.x/migrations).
