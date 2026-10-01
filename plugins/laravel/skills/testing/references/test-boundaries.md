# Test boundaries that affect correctness

## Laravel bootstrapping and authentication

Inspect `tests/TestCase.php`, Pest directory bindings, PHPUnit suite discovery,
and existing traits. Configure framework/database tests consistently with the
repository, typically under Feature unless another bootstrapped convention exists.
`RefreshDatabase` may reuse an up-to-date schema and wrap tests in transactions;
do not describe it as migrating every test class unconditionally.

Put guest tests outside a shared `actingAs()` setup, or use an established
guard-specific reset in the project's tests. Do not assume `withoutAuth()` exists.
For JSON APIs use JSON requests when testing JSON validation responses. Cover
authenticated-but-forbidden separately from unauthenticated.

## Data and effects

1. Prove the database connection is the isolated development/testing target before
   commands that refresh or truncate it. Preserve nondefault hosts and ports.
2. Check denied operations leave no forbidden record, event, job, or provider
   request. An HTTP status alone can miss an unauthorized side effect.
3. Use at least two tenants for isolation scenarios. Exercise guessed record IDs,
   related IDs, caches, and worker context where the changed behavior uses them.
4. Exercise concurrent state transitions against the appropriate database engine
   when concurrency is the claim. Sequential tests and SQLite do not prove row
   locking or production-engine semantics. Transaction-wrapped tests can also
   hide after-commit behavior; choose a suitable test boundary explicitly.
5. Freeze/control time for expiry and retry boundaries. Use relevant datasets for
   null, false, zero, empty strings, and limits rather than arbitrary input volume.

## External and UI evidence

Application adapter tests remain valuable even for a well-tested SDK. Verify
payload mapping, authentication configuration without exposing secrets, response
handling, idempotency and failure behavior. Use transport-appropriate fakes;
Laravel HTTP fakes do not intercept every third-party client's requests.

Sandbox tests need configured credentials and a controlled account. Keep them
outside the normal suite unless the project explicitly includes them. Check both
suite discovery and group filters: a group alone does not make an undiscovered
directory runnable, and an excluded group can still be excluded by the selected
configuration. Verify the actual command before documenting it.

Component tests prove component behavior. Browser tests establish rendered
interactions. Provider sandbox tests establish a remote integration. Report these
separately, and do not infer production verification from any local result.

Sources: [Laravel testing](https://laravel.com/docs/13.x/testing),
[database testing](https://laravel.com/docs/13.x/database-testing), and
[Pest test configuration](https://pestphp.com/docs/configuring-tests).
