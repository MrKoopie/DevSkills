# DevSkills

## Installation

See the [installation guide](INSTALL.md) for Codex App and CLI,
Claude Code, Cursor, Factory Droid, GitHub Copilot CLI, Kimi Code and Gemini CLI.
Codex and Claude provide all plugins; the other packaged clients currently
provide Feedback Triage.

## Git Workflow

[Pre-push Sync](plugins/git-workflow/skills/pre-push-sync/SKILL.md) fetches the target
branch, checks incoming changes for their impact, integrates them, adapts the work,
and validates before an authorized push. Invoke `pre-push-sync` before pushing.
The `git-workflow` plugin shares one source across Codex and Claude.

## App Modernization

[App Modernization](plugins/app-modernization/README.md) adds `modernize-app` and
`app-behavior-baseline` for staged app rewrites with actual screenshots, Mermaid,
technical/dependency inventories and executable behavior comparisons. Browser and
business scenarios run before rewriting; English code and purpose IDs such as
`F001-ADD-USERS` keep implementation and evidence consistent. It composes available
framework skills and the existing independent original-request validator.

Codex and Claude share the same source. Detailed references load only when needed;
generated evidence stays local and ignored. See the plugin's [usage and validation](plugins/app-modernization/README.md).

## Laravel

[Laravel](plugins/laravel/README.md) provides six skills: architecture (including
safe refactoring), implementation and review, testing, API contracts, Filament,
and pre-commit migration/code-quality checks.
The Codex and Claude marketplace catalogs share one source under `plugins/laravel`.
The plugin contains no agents or delegation requirements. Project discovery is a
short shared checklist, and detailed guidance is loaded only for the task at hand.

See the [skill inventory and usage](plugins/laravel/README.md) and
[validation scenarios](plugins/laravel/tests/scenarios.md). Run its package checks
with `python3 -m unittest discover -s plugins/laravel/tests -p 'test_*.py' -v`.
Catalog registration prepares distribution; it does not install or publish the plugin.

## Feedback Triage

[Feedback Triage](plugins/feedback-triage/skills/process-pr-feedback/SKILL.md) processes GitHub pull request and GitLab merge request feedback. It retrieves all pages through `gh` or `glab`, checks each distinct claim against the current code, scores valid suggestions, replies in each existing review thread with the pushed fix commit or a reason for not implementing, and then resolves addressed threads where possible.

1. Install or load the plugin from `plugins/feedback-triage` in your agent harness.
2. Invoke `process-pr-feedback` with a PR or MR URL, or provide the provider, full repository path, and number.
3. Use `python3 plugins/feedback-triage/scripts/fetch_feedback.py github --repo OWNER/REPO --number 123` or `python3 plugins/feedback-triage/scripts/fetch_feedback.py gitlab --repo GROUP/PROJECT --number 123` for a read-only feedback inventory. Add `--host HOST` for a self-managed instance.

The command paths in this README assume a DevSkills checkout and must be run from its root. If the plugin is installed separately, replace `plugins/feedback-triage` in each command with the absolute path to that installed plugin directory.

The value score is 0–100: impact 30, likelihood 20, scope fit 15, durability 15, effort 10, and safety 10. Only independently validated claims receive a score. Scores of 75 or more generally warrant implementation; 50–74 need a tradeoff decision; lower scores are normally deferred. Verified security, data loss, correctness, and contractual issues require explicit consideration regardless of score.

## Original request validation

[Validate Original Request](plugins/feedback-triage/skills/validate-original-request/SKILL.md) audits an implemented change against its original work item or a user-confirmed conversation brief. Three fresh native subagents separately review functionality and UX, end-to-end business/user processes, and technical quality. The primary validator exercises feature flows and wrong inputs, adds missing negative tests to the project's normal suite, and reconciles all three reviews in one local report under `.ai/triage/`. For visual changes, the report embeds actual browser screenshots of normal, error, and recovery states alongside correlated background I/O. Generated reports and screenshots stay out of Git.

1. Load the `feedback-triage` plugin in a harness with native subagent support, then invoke `validate-original-request` with the target repository, base/head commit SHAs, and issue URL or identifier when available. Supply project run instructions and the available browser environment.
2. For GitHub or GitLab, the parent collects the complete issue and comments with `python3 plugins/feedback-triage/scripts/fetch_issue.py github --repo OWNER/REPO --number 123` or the corresponding `gitlab` command. Add `--host HOST` for a self-managed instance. Other trackers require an available CLI or connector. If the issue is missing, inaccessible, or incomplete, the parent presents a reconstructed full-conversation brief and waits for your confirmation before launching the subagents.
3. Review the single report's functional, UX, business/process, and technical verdicts, blocking findings, and any new project tests. Before committing validation-related source changes, run `python3 plugins/feedback-triage/scripts/check_validation_artifacts.py --repo PATH` to reject staged or tracked `.ai/triage/` artifacts.

## Validation harness capabilities

Capability snapshot for the original single-validator route: **2026-09-24**. `verified` means a real native subagent completed that part of a disposable fixture run; `unavailable` means this host could not execute it; `untested` means there is no execution evidence. These rows do not prove that the newer three-reviewer orchestration works in a harness. Documentation and descriptor discovery alone do not verify an independent audit. Browser routes below are documented options, all untested here because the fixtures were nonvisual. A visual audit still needs an embedded screenshot for each affected normal, error, and recovery state, with background I/O correlated to that browser step. The UX assessment applies to nonvisual journeys too.

| Harness | Subagent launch | Compact handoff | Returned report | Browser route | Host evidence |
| --- | --- | --- | --- | --- | --- |
| Codex App / CLI | verified (App, CLI) | verified (App, CLI) | verified (App, CLI) | untested | App native `spawn_agent` exercised on synthetic briefs and paginated issue fixtures. CLI 0.154.0 with `gpt-5.5` launched one fresh-context child in a disposable Python fixture; the child returned a matching source/SHA Fail report and added a failing negative test. CLI browser route remains untested. |
| Claude Code | verified | verified | verified | untested | `claude --version`: 2.1.263; `claude -p --plugin-dir ./plugin` fixture launched one child, returned a matching source/SHA report and Pass, and ran 15 tests. Empty-diff baseline smoke only. |
| Cursor | unavailable (agent CLI) | untested | untested | untested | `cursor --version`: editor 2.1.46. `cursor agent --help` reported missing cursor-agent, then failed its automatic download with DNS error; no agent run. |
| Factory Droid | untested | untested | untested | untested | `command -v droid`: absent. |
| GitHub Copilot CLI | untested | untested | untested | untested | `command -v copilot`: absent. |
| Kimi Code | untested | untested | untested | untested | `command -v kimi`: absent. |
| Gemini CLI | untested | untested | untested | untested | `command -v gemini`: absent. |

Three-reviewer update, **2026-09-25**: Codex App launched the read-only business and technical reviewers with matching source, head SHA, and clean-tree snapshot, then launched the primary independently and reconciled their returns into one ignored report at the validated revision. This verifies the nonvisual three-role route in Codex App for this repository. Visual evidence and the three-role route in the other harnesses remain untested.

Use the loaded harness's native tool schema. `HANDOFF` below means the same compact JSON for all three roles, including the exact pre-existing working-tree manifest when the target is dirty. `CONTRACT` means the installed path to the corresponding [primary](plugins/feedback-triage/skills/validate-original-request/references/subagent-contract.md), [business/process](plugins/feedback-triage/skills/validate-original-request/references/business-process-contract.md), or [technical](plugins/feedback-triage/skills/validate-original-request/references/technical-contract.md) contract. For named agent tools, dispatch `validate-business-process` and `validate-technical-implementation` from the parent and wait for both before dispatching `validate-original-request`. Reconcile their returns in the one report. The parent handles orchestration because some harnesses prohibit nested subagents. Resolve the source and any required user confirmation before dispatch. If a required role cannot run, disclose the missing review and do not claim a complete audit verdict.

| Harness | Documented dispatch and adapter | Documented visual route (not execution proof) |
| --- | --- | --- |
| Codex | Current V2 `spawn_agent({task_name: "original_request_audit", fork_turns: "none", message: "Read CONTRACT and audit HANDOFF"})`; use the native wait/return tools. Older tool schemas differ; never pass an unsupported history flag or inherit the full conversation. [Official tool implementation](https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs). | An available browser tool in the App, or a configured browser MCP server in CLI; inspect the actual child tool surface. [MCP configuration](https://developers.openai.com/codex/mcp). |
| Claude Code | Load `--plugin-dir /absolute/plugin/path`; ask “Use the feedback-triage:validate-original-request subagent with HANDOFF.” Native `Agent` (named `Task` by this installed build) takes `subagent_type`, `description`, and `prompt`. The plugin's `agents/validate-original-request.md` supplies the contract. `--agent` alone selects the main agent and does not prove delegation. [Subagents](https://code.claude.com/docs/en/sub-agents), [plugin agents](https://code.claude.com/docs/en/plugins-reference). | Configured Playwright MCP inherited by the child, or Chrome integration where available. [Browser MCP example](https://code.claude.com/docs/en/sub-agents), [Chrome](https://code.claude.com/docs/en/chrome). |
| Cursor | Ask Agent “Launch a fresh subagent to read CONTRACT and audit HANDOFF; return the contract return block.” Use its exposed task tool; official ACP `cursor/task` is a notification, not a callable launcher. No extra plugin descriptor is required for task-prompt delegation. [Subagents](https://cursor.com/docs/subagents), [ACP](https://cursor.com/docs/cli/acp). | Built-in browser subagent / browser MCP. Verify availability to the validator and return correlated evidence. [CLI MCP](https://cursor.com/docs/cli/mcp). |
| Factory Droid | `Task({subagent_type: "validate-original-request", description: "Validate original request", prompt: HANDOFF})`; plugin discovery uses `droids/validate-original-request.md`. [Task schema](https://docs.factory.ai/cli/configuration/custom-droids), [plugin layout](https://docs.factory.ai/guides/building/building-plugins). | Configured MCP or `agent-browser` through the shell; separately collect correlated I/O. [Automated QA](https://docs.factory.ai/guides/skills/automated-qa). |
| GitHub Copilot CLI | `task(agent_type="validate-original-request", ...)` with HANDOFF as the task prompt in the loaded tool schema; plugin `agents/` accepts `.md` as well as `.agent.md`, so the shared descriptor suffices. Verify discovery using `/agent`. [Plugin agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating), [CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference), [task dispatch](https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/fleet-mode). | Configured browser MCP; inspect tools with `copilot mcp get NAME`. Do not assume the cloud agent's default Playwright setup exists in CLI. [CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference). |
| Kimi Code | `Agent({subagent_type: "validate-original-request", description: "Validate original request", prompt: HANDOFF})`; plugin discovery uses the shared `agents/` descriptor. [Agent tools](https://github.com/moonshotai/kimi-code/blob/main/docs/en/reference/tools.md), [plugin discovery](https://github.com/moonshotai/kimi-code/blob/main/docs/en/customization/plugins.md). | A configured browser MCP server inherited by the child; no browser is bundled here. [MCP/plugin configuration](https://github.com/moonshotai/kimi-code/blob/main/docs/en/customization/plugins.md). |
| Gemini CLI | Extension `agents/*.md` exposes each agent as a tool of its declared name. Call the discovered `validate-original-request` tool with HANDOFF in its task input; inspect its generated schema. The shared descriptor needs no extra extension-local path. [Extension reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md), [subagents](https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md). | Grant a configured browser MCP to the validator. The optional `browser_agent` is disabled by default and subagents cannot call other subagents, so enabling it alone does not give the validator visual proof. [Subagents and browser configuration](https://github.com/google-gemini/gemini-cli/blob/main/docs/core/subagents.md). |

The shared agent and Factory droid descriptors omit tool allowlists deliberately: their documented defaults inherit tools for shell tests and configured MCP access. The primary role owns normal-suite test edits, local reports, and browser proof; the two specialist roles are read-only. Each descriptor points to its contract rather than duplicating the procedure. Host policy can still restrict tools; missing required proof remains Unverified. The [report template](plugins/feedback-triage/skills/validate-original-request/references/report-template.md) and artifact guard apply to every harness.

## Distribution catalogs

The marketplace files reference the same `plugins/feedback-triage` source. The
Codex and Claude catalogs additionally include `plugins/laravel`,
`plugins/app-modernization`, and `plugins/git-workflow`; the other
catalogs currently contain Feedback Triage only:

| Harness | Catalog or extension file |
| --- | --- |
| Codex App and CLI | `.agents/plugins/marketplace.json` |
| Claude Code | `.claude-plugin/marketplace.json` |
| Cursor | `.cursor-plugin/marketplace.json` |
| Factory Droid | `.factory-plugin/marketplace.json` |
| GitHub Copilot CLI | `.github/plugin/marketplace.json` |
| Kimi Code | `kimi-marketplace.json` |
| Gemini CLI | `plugins/feedback-triage/gemini-extension.json` (extension manifest; no marketplace file) |

Grok Build and Qwen Code can consume the Claude Code marketplace format. Superpowers also documents Antigravity, Devin CLI, OpenCode, Pi, Hermes Agent, and Muse; those use repository installs, packages, or native plugins rather than one of these repository marketplace JSON formats. Their native distribution paths would need separate packaging and validation before claiming support.

These files prepare the local catalogs. They do not publish the plugin to any hosted marketplace or install it in an agent harness.
