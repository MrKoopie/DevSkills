# Laravel

Five skills for Laravel application work, shared by Codex and Claude Code. This
plugin includes no agents, delegation requirements, hooks, MCP servers, or package
installation scripts. All workflows can be performed directly by the current
assistant.

| Skill | When it earns its place | Distinct result |
| --- | --- | --- |
| [architecture](skills/architecture/SKILL.md) | Domain ownership, structural refactoring, or package extraction | Existing-context comparison, scope/placement map and safe change sequence; refactors reconcile completion while ordinary edits retain existing structure. |
| [implement](skills/implement/SKILL.md) | Application behavior, jobs, queries, policies, Livewire, or implementation review | Correct behavior using native Laravel facilities, including failure and concurrency boundaries. |
| [testing](skills/testing/SKILL.md) | Tests, regression coverage, or requirement verification | Observable evidence in the project's existing Pest/PHPUnit setup. |
| [api](skills/api/SKILL.md) | Endpoints, compatibility, versioning, documentation, or retirement | A preserved or intentionally changed public contract with client-facing evidence. |
| [filament](skills/filament/SKILL.md) | Admin UI, panel actions, tenancy, or Filament upgrades | Version-correct component behavior with server-side authorization and useful UI states. |

## How they interact

Select the skill that owns the requested outcome. It reads the short shared
[project-context checklist](references/project-context.md) once as needed, then
loads only relevant references or sibling skills. A Filament label edit does not
need architecture; a panel action with new business logic may also use implement;
an API change may use testing for its contract evidence. Review modes and the
shared [verification procedure](references/verification.md) transfer the useful
developer/reviewer agent guidance into skills.

Project context is not an automatic startup hook. Skills explicitly read it when
the relevant facts are missing or have changed. Refactoring is a mode within
architecture, not a sixth skill. Installing this plugin does not require enabling
every skill for every request.

## Distribution

The DevSkills Codex and Claude catalogs point to this directory. The Codex manifest
is `.codex-plugin/plugin.json`; the Claude manifest is `.claude-plugin/plugin.json`.
Both clients consume the same five `skills/*/SKILL.md` entry points. Their display
and invocation syntax depends on the client; the intended plugin namespace is
`laravel`, for example `laravel:api`. Verify discovery after installation.

These files prepare distribution; they do not publish to a hosted marketplace,
install globally, or replace existing personal skills. Existing standalone or
synced Laravel skills can supply competing instructions until explicitly retired.
Only Codex and Claude packaging is included for this plugin.

## Consolidation decisions

1. Merge Laravel patterns, best practices and DDD coding into implement; retain
   targeted references for data, tenants, jobs, integrations and Livewire.
2. Merge DDD architecture and modular refactoring into architecture. Retain
   package-consumer proof and persisted-class migration concerns; remove fixed
   folder trees and universal abstraction rules.
3. Preserve behavioral testing while supporting Pest, PHPUnit and mixed suites.
   Keep application adapter tests even when a provider SDK has tests.
4. Preserve API compatibility/deprecation guidance and Filament UI/tenancy
   guidance; replace copied API catalogs with version-aware documentation lookup.
5. Transfer developer and reviewer responsibilities into implementation/review
   modes and shared verification. Remove persona claims, model choices, forced
   questions, agent dispatch, automatic commits/PRs and unrelated workflow tools.
6. Correct known examples: false/zero query filters, first-versus-last match,
   transition checks versus atomicity, event dispatch, Composer tilde constraints,
   authentication test setup, deprecation headers and relationship query scoping.

Domain modeling rules are explicit in the architecture reference and reachable
directly from implement: business vocabulary, bounded contexts, action composition
and injection, typed immutable DTOs, rich models, value objects, builders, events
and entry-point responsibilities. Import-specific ownership and schema decisions
have a separate reference. Original rigid folder/package mandates are adapted to
project conventions; the DDD responsibilities themselves remain available.

For layered context work, the [Company example](skills/architecture/references/layered-context-example.md)
shows a selected Application/Domain/Infrastructure layout, full responsibility map,
guarded direct CRUD and explicit transaction guarantees. Refactor completion also
checks residual models, services and UI logic against the original scope; passing
behavior checks alone does not establish architectural completeness.

## Validation

From the repository root:

```sh
python3 -m unittest discover -s plugins/laravel/tests -p 'test_*.py' -v
```

The package tests verify relocatable references, catalog/manifest consistency,
skill discovery metadata and the skills-only boundary. The bundled Codex
plugin-creator and skill-creator validators can additionally validate their
respective manifests; they require a Python environment with PyYAML.

[Scenarios](tests/scenarios.md) specify realistic routing and application checks.
They are a reusable manual evaluation rubric, not automated behavioral evidence.
For a release, exercise relevant scenarios in an isolated fixture, save actual
outputs locally, and state whether evaluation was manual, model-driven, or an
application runtime test. Package checks do not prove a Laravel application or
client installation works. Keep generated evaluation reports out of commits.
