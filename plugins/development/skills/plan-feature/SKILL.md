---
name: plan-feature
description: Define and size functional requirements, confirm a functional flow with a working prototype, and present an independently reviewed database and file plan.
---

# Plan a feature

Save the requirements table, runnable prototype and reviewed plan as separate versions in the [local feature workspace](../../references/feature-workspace.md). Give the plan reviewer the exact candidate paths.

Work through the following three steps. Use the requester's language. Keep one
current requirements table. Whenever a requirement, flow, prototype or plan
changes, present the full requirements table again with the update. Reprint any
revised database or code table in full too. Keep accepted IDs stable so a
reviewer can follow a requirement from the first discussion to its test.

## 1. Define the functional changes

Read the user's request, linked sources, discussion and latest corrections.
Group each major change under a numeric major ID. Give each related observable
requirement its own secondary ID, e.g. `1.1`, `1.2`, `2.1`. Add new rows with
unused IDs. For each row identify the actor, action and expected outcome where
relevant. Rate its difficulty in the context of the existing application.

| Requirement ID | Functional requirement | Difficulty level | Description of change |
| --- | --- | --- | --- |
| 1.1 | Example: approve a quote | 🟡 C3 — Moderate | An authorized reviewer can change a pending quote to approved. |

Keep each description to one or two sentences. Include the code and label
together. Use the following anchors to choose a level.

| Difficulty | When it fits | Example |
| --- | --- | --- |
| 🔵 C1 — Very simple | Adjust existing behavior with understood consequences and no new rules. | Select an already-supported newest-first sort as the default. |
| 🟢 C2 — Simple | Extend an established pattern with few dependencies. | Add and store an optional form field. |
| 🟡 C3 — Moderate | Several rules or states interact within an established architecture. | Add approval statuses, role permissions and decision notifications. |
| 🟠 C4 — Complex | Multiple processes must coordinate ordering, consistency and partial failure. | Apply a plan change across subscriptions, billing and server configuration. |
| 🟣 C5 — Very complex | Ownership or system boundaries change while existing behavior must continue through a transition. | Introduce tenant isolation, migrate customer data and preserve integrations. |

Challenge prerequisites and omissions. For example, before planning quote
approval, check whether quotes already exist and who can approve them. List
unresolved gaps below the table against their IDs. Ask the user about material
choices. Add an inferred feature to scope only once agreed. Reuse requirements
the user has already confirmed. Present the whole table for confirmation or
correction before moving on, and redisplay it after each change.

## 2. Show the functional flow and prototype

Inspect the actual application, its coding style and the nearest related
journey. Create a simple left-to-right Mermaid flow (`flowchart LR`) showing the
actor's actions, meaningful decisions and visible outcomes. Use product terms.

Build a runnable prototype artifact that simulates the changed journey with
sample data. For a UI, a small clickable local HTML file can suffice. For a job
or API, a runnable input/output simulation can demonstrate success and relevant
rejection or recovery. Open or run the artifact, exercise the changed path and
report what worked. Give the user the diagram, a usable artifact link or local
entry point, and a short scenario to try. Identify simulated effects explicitly.
Ask the user to confirm the demonstrated behavior before technical planning.
If feedback changes the behavior, update the requirements table, flow and
prototype, and obtain confirmation of the revised version.

## 3. Prepare and validate the code plan

Identify the application type, installed framework, repository guidelines and
relevant application-specific skills. Trace the existing implementation and
nearest tests. Choose the simplest file changes that satisfy the confirmed
requirements. Link each file to its requirement IDs, including test files where
needed. Define a verification step for each ID.

Inspect the current schema and migration history when deciding whether data
changes are needed. Compare the branch to its base, including earlier commits
and local migrations. Prefer amending a compatible existing branch migration
when evidence shows it has not reached production or been shared or applied
in an environment that relies on its identity. Preserve order, constraints,
existing data and rollback behavior. If that status is unknown, call out the
uncertainty and plan a forward migration where needed. Planning leaves the
database and migrations untouched.

Make the plan usable by the person or agent writing the code. For each
implementation task include the requirement IDs, relevant paths, concrete code
change, applicable skill names and verification command or observable check.
For an authorized build, the implementer executes `development:build-and-test`,
applies the project-specific implementation and testing skills, edits the actual
product and tests, then runs `development:self-review`. For example, in Laravel
name `laravel:implement` and `laravel:testing`, plus API or Filament when relevant.
Carry these instructions into the executable plan and any Superpowers task brief.
Include a separate independent `development:technical-review` of the combined
change, then the functional/UX and PR feedback stages of the feature workflow.

Before showing the code plan, give a fresh read-only native subagent the source,
confirmed requirement IDs, confirmed flow and prototype version, checkout/base
and local changes, draft database/file tables and proposed checks. Use
`review-feature-plan` when the client requires a named role. Have the reviewer
check gaps, simplicity, migration evidence, actual paths, scope and testability
against the repo. Process findings and have material revisions rechecked.
Present the plan once the current version passes. If independent review cannot
finish, report the outstanding question or unavailable check.

Present the result compactly, using these layouts:

- **Database changes: None** when the existing schema suffices.
- **Database changes are required** otherwise. Under **Table <name>** for
  each affected table, list each affected column, its type and why it changes.
  Identify any schema-level operation such as an index alongside its table.

| Column name | Type | Reason |
| --- | --- | --- |

**Code changes**

| Filename | State (new/modify) | Related feature ID | Purpose of file |
| --- | --- | --- | --- |

Use repository-relative paths and one row per file. Close with the per-ID
checks and independent verdict. If implementation reveals a simpler workable
approach, update the full tables and revalidate material technical changes.
A changed functional outcome also reopens user confirmation.
