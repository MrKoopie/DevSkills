# Jobs and external integrations

1. Use Laravel job failure handling: appropriate attempts, backoff, timeout,
   retry-until policy, failed-job recording, and `failed()` when a terminal effect
   is needed. Catch only failures that are actually handled; swallowing an
   exception can make a failed operation look successful. Do not build a parallel
   retry/recovery framework to replace the queue's native lifecycle.
2. Configure worker timeout and connection retry visibility coherently for the
   actual driver. Verify after-commit dispatch where a job reads newly committed
   records. Job uniqueness or overlap middleware is not proof that an external
   side effect occurs exactly once.
3. Make duplicate delivery safe with an operation identity, appropriate database
   constraints/state, and the provider's idempotency support where available.
   After a timeout on a remote write, reconcile by the same identity/reference
   before another attempt. Business reconciliation complements native job retries;
   it does not replace them.
4. Validate webhooks using the provider's documented raw-body signature procedure
   and replay/timestamp rules. Persist and deduplicate event identity as needed.
   Handle duplicate and out-of-order delivery without repeating business effects.
5. For imports, isolate provider payload mapping from local business rules. Key
   imported records by tenant/source plus external identity, preserve local-owned
   fields, and record progress so retrying a page does not duplicate writes. Keep
   locale identity and parent relationships explicit where the source has them.
   Do not infer deletion from an incomplete page or failed synchronization.
   For integration structure and persistence choices, read
   [import boundaries](import-boundaries.md).
6. Test the application's adapter mapping, timeouts, malformed responses, retry
   behavior and duplicate handling even when an SDK has its own test suite. SDK
   tests do not establish that the application uses it correctly. Use targeted
   transport fakes and prevent unintended network calls in normal tests.
7. Use provider sandbox tests only when needed and configured for the task. Label
   fake-based, sandbox, and production evidence separately. Never log credentials,
   signed URLs or complete sensitive payloads as debugging evidence.

For operational changes, inspect actual supervisor/worker/scheduler configuration,
configuration caching and restart requirements. Running a local test does not
establish that production workers picked up a change; deployment requires its
own authorized scope and evidence.

Source: [Laravel queues](https://laravel.com/docs/13.x/queues).
