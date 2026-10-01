# App Modernization

Two skills shared by Codex and Claude Code, with no Superpowers dependency:

| Skill | Outcome |
| --- | --- |
| [modernize-app](skills/modernize-app/SKILL.md) | Coordinate scoped rewrites, phased implementation, comparison and independent final validation. |
| [app-behavior-baseline](skills/app-behavior-baseline/SKILL.md) | Capture and replay visual journeys, technical operations and dependencies; compare candidate behavior. |

Use the baseline skill alone for discovery or comparison. Use the orchestrator for a
rewrite: required browser and business scenarios run before product changes, including
structural refactoring. Known defects receive correction criteria; missing proof remains
visible. English code/documentation and IDs such as `F001-ADD-USERS` are required while
supported product localizations and compatibility remain covered.

Records use a short index and selectively loaded evidence under the target repository's
ignored `.ai/triage/modernize/`. Reusable application tests stay in the normal suite.
See [artifact rules](references/artifacts.md) for naming, replayable snapshots and guards.

## Companions and clients

The independent final audit requires the available `feedback-triage` plugin's
`validate-original-request` skill and native subagents. Baseline capture works without
that companion; a missing final audit prevents a complete independent verdict. Laravel
rewrites use the available `laravel` architecture/implement/testing skills. Other frameworks
use their own specialist guidance. Companions are discovered, not installed automatically.

Claude discovers [baseline-discovery](agents/baseline-discovery.md) in `agents/`.
Codex dispatches the same [contract](references/discovery-contract.md) through its exposed
native subagent tool. See [delegation](references/delegation.md). No model is hardcoded.
The Codex and Claude repository catalogs register this plugin; other harness catalogs
are unchanged. Registration does not install or publish it. Browser/host capability must
be demonstrated separately; a manifest or package test does not prove live client behavior.

## Validation

From the DevSkills repository root:

```sh
python3 -m unittest discover -s plugins/app-modernization/tests -p 'test_*.py' -v
```

These checks verify relocatable references and distribution consistency, not application
behavior. [Evaluation scenarios](tests/scenarios.md) define behavioral probes for isolated
agent runs; keep their actual outputs local and report executed versus untested cases.
