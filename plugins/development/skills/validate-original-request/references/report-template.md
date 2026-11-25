# Original request validation

Source: <confirmed issue or conversation brief>
Target: <repository, base SHA, head SHA>
Environment: <runtime and test commands>

## Requirements overview

| ID | Requirement | Source | Feature/flow | Evidence | Verdict | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | <original question or criterion> | <URL/comment or confirmed brief section> | <feature and flow ID> | <command/result, probe, or visual step> | <Pass/Partial/Fail/Unverified> | <concise explanation> |

## Feature flows

Source retrieval: <timestamp, source links, last modification time, pagination completeness, latest explicit corrections, conflicts>

Audit timestamp: <local time and timezone>

Revision binding: <checkout HEAD check; pre/post working_tree_snapshot of path, Git status and SHA-256 or deleted for every pre-existing change; separately listed added/modified normal-suite test files; drift outcome>

Running application revision: <observable build/deployment identifier matching audited head and scoped product snapshot, or Unverified and excluded from Pass evidence>

Feature inventory: <every new feature and changed input boundary, including behavior without a source requirement>

### F1: <feature and intended actor>

Prerequisites and entry point: <role, authorization, tenant, navigation or command>

Flow judgment: <whether the actor can reach the goal; discoverability, coherence, effort, feedback, error clarity, safe exit and recovery; distinguish functional from UX observations>

| Step | Actor | Input | Expected | Actual | State transition | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | <role> | <action or data> | <observable result> | <observed result> | <before to after> | <test/probe/visual reference> |

Functional proof: <actual command, exit status, relevant output, live observation, and inference limits>

## UX assessment

UX conclusion: <Does the solution make sense to its intended users? State the main evidence and the largest friction or proof gap. A functional Pass alone is not a UX Pass.>

| Journey/actor goal | Entry and expected path | Observed steps and outcome | Friction or confusing state | User consequence | Evidence | UX verdict | Recommended change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <F1 / what the actor is trying to achieve> | <where they start, expected next actions> | <actual sequence, completion or exit> | <specific terminology, order, effort, feedback, error or recovery issue; or none observed> | <why it matters to this actor> | <flow step, CLI/browser probe, screenshot> | <Pass/Partial/Fail/Unverified> | <concrete improvement or none> |

Evaluate every affected journey, including nonvisual CLI/API flows. Check discoverability, terminology, number and order of actions, waiting/completion feedback, error clarity, next action, safe recovery, and accessibility/responsive behavior where relevant. Name a concrete observed consequence for each UX defect; do not score personal visual taste as a defect. For visually changed journeys, cite the normal, error, and recovery screenshots below. If the browser or a required screenshot is unavailable, mark the visual UX proof Unverified.

## Business and user process assessment

Independent reviewer: <source identifier, retrieval/modification times and completeness, head and pre-existing working_tree_snapshot match; or pending during primary first pass>

Business/process conclusion: <Does the end-to-end process reach the original user or business goal across actors and systems? State verdict and evidence limits.>

| Process and actor goal | Trigger and eligibility | Expected states, handoffs, and completion | Observed path | Exception and recovery | Evidence and user/business consequence | Process verdict | Gap or action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <P1 / actor goal> | <source-based entry and policy> | <owners, state changes, side effects, completion> | <what the change actually does> | <cancellation, retry, partial failure, or not applicable> | <source criterion; verified trace; concrete consequence> | <Pass/Partial/Fail/Unverified> | <specific change, proof, question, or none> |

Cover every material process implied by the diff, including role handoffs and side effects; give a row even when it passes. Process Pass requires executed or observed behavior, not code presence alone. Record policy questions without inventing rules. Identify specialist findings not adopted after evidence verification and explain why. The specialist does not write a separate report.

## Technical validation

Independent reviewer: <source identifier, retrieval/modification times and completeness, head and pre-existing working_tree_snapshot match; or pending during primary first pass>

Technical conclusion: <Does the implementation preserve required contracts and material failure boundaries? State verdict and evidence limits.>

| Component and flow | Technical boundary | Expected contract or invariant | Observed behavior or risk | Evidence and proof level | Kind and severity | User impact | Technical verdict and action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <component / flow> | <architecture, trust, data, dependency, compatibility, or operation> | <source or established project invariant> | <reproduced result or clearly marked risk> | <file:line, command, exit, local/integrated/live> | <verified check/observed defect/plausible risk/missing proof; severity> | <concrete consequence or none> | <Pass/Partial/Fail/Unverified; fix or probe> |

Cover every material changed component and boundary with a row, including passing checks; separate reproduced defects from unverified risks and style preferences. A component list or code inspection alone cannot establish technical Pass. Record specialist findings not adopted after evidence verification and explain why. The primary validator owns any added normal-suite negative tests and the single report.

## Wrong-input and failure tests

| Feature/input boundary | Case and risk | Expected | Actual | Project test file | Command and result | Requirement/verdict |
| --- | --- | --- | --- | --- | --- | --- |
| <changed input> | <omission, malformed, limit, auth/tenant, duplicate/stale, dependency failure as applicable> | <defined failure behavior> | <observed behavior> | <normal suite path or missing reason> | <exact command, exit status, result> | <ID and verdict> |

Product defect handoff: <reproduction, expected and actual, test path and command, implementing-agent action; or none>

Missing or blocked checks: <specific check, reason, affected requirement, next action; or none>

## Visual walkthrough and correlated background I/O

Visual scope: <affected UI surfaces or “No visual behavior changed; browser not opened.”>

Viewport and environment: <browser, viewport, app version/URL, test identity with secrets redacted>

| Flow/step | State | Actor and input | Expected UI | Actual UI and UX observation | Screenshot asset | Background request input | Background response output | Correlation and state transition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <F1/1> | <normal/error/recovery> | <role/action> | <visible state> | <observed state and whether the next action is clear> | `<HH-MINUTE-assets/F1-1-normal.png>` | <method/path and redacted payload, or verified no request sent> | <status and redacted result, or verified no request sent> | <request ID, or method/path + narrow timestamp + matching response; before to after> |

For **each** row, repeat a figure block immediately below the table so the screenshot is visible in the Markdown report, not just linked as a filename:

### <F1/1 — normal, error, or recovery state>

<caption: actor action, observed state, viewport, and correlation ID>

![<descriptive state and error text when applicable>](<HH-MINUTE-assets/F1-1-normal.png>)

Capture a real browser screenshot after each affected normal, error, and recovery state appears. Error screenshots must show the visible error and enough surrounding UI to understand what the user entered and can do next. Use safe fixture data or redact sensitive content without obscuring the relevant UI. If a validation error is entirely client-side, verify that the interaction sent no matching network request and record `no request sent` in both background columns. A timestamp alone does not correlate concurrent requests: use an ID, or method/path plus a narrow time window and matching response. Do not use a screenshot of another state, generated illustration, test output, or a bare path as visual proof. If a required visual check or screenshot is unavailable or unreadable, name the state and reason and mark its visual and UX proof Unverified. For nonvisual changes state “No visual behavior changed; browser not opened” and do not add placeholder images.

## Gaps and overall verdict

Functional verdict: <Pass/Partial/Fail/Unverified and reason>

UX verdict: <Pass/Partial/Fail/Unverified and reason, including visual proof limits>

Business/process verdict: <Pass/Partial/Fail/Unverified and reason>

Technical verdict: <Pass/Partial/Fail/Unverified and reason>

Overall verdict: <Pass/Partial/Fail/Unverified and reason; account for all four reviews and any disagreement>

Evidence summary: <separate local test, live behavior, UX observations, visual screenshots, business process traces, and technical probes>

Gaps, risks, and open questions: <requirement ID, effect on verdict, and next action; or none>

Report path: `.ai/triage/YYYY-MM-DD/HH-MINUTE-report.md`; generated evidence: `.ai/triage/YYYY-MM-DD/HH-MINUTE-assets/`. Use the local 24-hour clock. Resume by updating this run's report. If a distinct run begins in the same minute, wait until the next minute before allocating its report/assets names. Never commit these generated files.
