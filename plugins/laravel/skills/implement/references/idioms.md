# Idioms must preserve behavior

Use a Laravel helper when it expresses the same contract more clearly. Shorter
syntax is not sufficient justification for a refactor.

1. `Collection::first()` replaces a search for the first match. A loop that keeps
   assigning on each match returns the last match; preserve that difference unless
   the task explicitly fixes it. Avoid materializing a large stream just to use
   a collection helper.
2. `findOrFail()` or route binding expresses missing-record 404 behavior in an
   HTTP flow. Keep explicit handling when a missing record means a redirect,
   no-op, domain error, or different response. Preserve tenant scoping before
   retrieval; finding a record is not permission to access it.
3. Conditional queries must preserve valid false/zero values. When the contract
   says only null means no filter, the condition remains explicit:

   ```php
   $query->when(
       $status !== null,
       fn ($query) => $query->where('status', $status),
   );
   ```

   The closure captures `$status`: the value passed by `when()` would be the
   boolean condition here. Preserve `!== ''` for a search where `"0"` is valid.
4. `rescue()` is appropriate only when reporting an exception and returning a
   fallback is the intended outcome. Do not use it to hide a failed queued job,
   authorization failure, or uncertain external write. Keep typed catches when
   failures have different meanings.
5. Model a fixed set of distinct outcomes with an enum; use a result DTO when
   there is associated data. A genuinely binary predicate can remain a boolean.
   Avoid introducing a result type solely to wrap an unused option.
6. Put actor-dependent rules in policies. Put state-transition invariants in the
   operation/transition that every writer executes, including direct callers.
   A state-machine guard does not itself make a read/check/write atomic or
   justify removing a database lock.
7. Prefer the installed framework's event dispatch conventions. A plain event
   object can be passed to `event(new OrderShipped($order))`; static
   `OrderShipped::dispatch()` requires the event's `Dispatchable` trait or an
   equivalent method. Select after-commit semantics for effects that depend on
   committed data.

Source: [Laravel query builder](https://laravel.com/docs/13.x/queries).
Check the project's installed version before adopting version-specific APIs.
