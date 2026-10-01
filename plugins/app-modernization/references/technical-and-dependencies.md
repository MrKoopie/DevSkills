# Technical execution and external dependencies

Enumerate console commands/options, schedules, job classes and dispatchers, queues,
events/listeners, APIs/webhooks, storage/database boundaries and runtime processes.
Include conditional/environment-only paths and jobs defined but not dispatched. Map
every discovered entry to a technical/flow record or reasoned exclusion; technical
operations without UI still need scenario coverage. Inspect source and safe listing/help
output first; execute mutations only within authorized isolated fixtures.

| Field | Compact technical record |
| --- | --- |
| Identity | Full technical ID, responsibility, flow/dependency IDs, code/config references |
| Trigger | Command/options, schedule, event or dispatch; actor/authorization |
| Execution | Input → components → output, persistence and external effects |
| Async | Connection/queue, delay, timeout, retry/backoff and failure handling |
| Boundaries | Relevant transactions, locks, idempotency, tenancy and after-commit behavior |
| Operation | Worker/scheduler/runtime requirements, logs, monitoring, recovery |
| Proof | Reproduction command, exit/output/assertions and evidence status |

Distinguish observed configuration from defaults and inferred production configuration.
Test actual workers where delivery is claimed; a queued/faked dispatch is a different
proof boundary. Use the appropriate database/runtime when asserting concurrency or
production-specific semantics. Record unresolved operational facts explicitly.

Treat localization as a contract. Inventory supported locales and translated outcomes;
compare locale coverage after English renaming and exercise affected normal/error states
in supported non-English locales. Map renamed keys. Silent fallbacks or internal names
leaking into translated validation/errors are regressions.

Use one dependency table: purpose ID, dependency/version, purpose/callers, required or
optional, contract, configuration variable names, failure behavior, hosting/runtime
constraints, verification status/evidence. Include services/APIs, SDKs, external binaries,
databases, queue/storage/mail backends and browser assets. Link lockfiles for exhaustive
package inventories; detail libraries whose behavior or compatibility matters to the rewrite.
Never include credential values. Distinguish fakes, local emulators, provider sandboxes
and real-provider evidence; successful mocks cannot establish remote behavior.
