# Executable comparison scenarios

A scenario describes behavior: Given preconditions, When an action happens, Then
observable results and effects follow. Browser, feature/integration and unit tests
execute assertions at different boundaries. Link each test to its flow/state/technical
IDs. One scenario may use multiple layers for different proof without repeating every
assertion. Follow the project's runner and framework testing skill.

1. Before any product rewrite, including moves/renames, create and run the required
   browser and scenario/feature tests for the agreed scope. Prioritize real journeys
   and business outcomes. Cover meaningful denied/invalid/failure/recovery cases and
   operations without UI. Existing pure calculation/rule tests protect stable contracts;
   new implementation-specific unit tests can be written with the new implementation.
2. Establish explicit expected outputs using authoritative requirements and observed
   baseline evidence. Legacy output is not automatically correct. Use shared synthetic
   fixtures, controlled time and isolated persistence; record runner commands, versions,
   fixture hashes and results. No testing against real customer data. Expected fixtures
   must not be regenerated from the candidate merely to make comparisons pass.
3. Compare semantic outputs: amounts, authorization, responses, persisted state, generated
   documents and external effects. Normalize only documented incidental values such as
   generated IDs, not meaningful timestamps, ownership or business values. Assert that
   denied actions leave no forbidden data, job or provider effect. Screenshots complement
   backend assertions; job dispatch/provider fakes prove only their local boundary.
4. Record pass/fail/setup-blocked per scenario. For confirmed defects, preserve observed
   behavior as evidence and add a correction criterion with a test failing on baseline
   and passing on candidate. A fixture/environment failure is not that regression.
   Fix setup gaps by default. Only the user may waive named missing proof or change
   scope; record the decision and keep the evidence unverified. Never silently skip,
   weaken assertions, or label a partial run passing to start rewriting.
5. Preserve baseline code, test/adapter revisions and fixture material so both versions
   can be replayed. Maintain scenario inputs and business assertions across the rewrite.
   Selectors, setup and internal adapters may change with recorded reasons; expectations
   change only for agreed improvements. Internal unit tests may change while their
   critical business guarantees survive. Run candidate tests at its recorded revision.
6. When persisted names/schemas/serialized classes change, seed baseline-format records
   and affected pending work, run the actual upgrade/compatibility path, then exercise
   candidate scenarios on the migrated state. Fresh candidate fixtures do not prove
   upgrades. Exercise relevant restore/rollback or forward-recovery paths when release
   readiness depends on them. Keep supported localizations covered after English renaming.

Minimal scenario row: ID | Given/input fixture | When/action | Then/outputs and forbidden
effects | browser/feature/unit test references | baseline result | candidate result | evidence.
Keep executable tests in discoverable normal suites; generated reports/screenshots remain
ignored. Record explicit completion conditions for async work rather than arbitrary sleeps.
