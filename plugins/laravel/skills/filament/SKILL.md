---
name: filament
description: Use when implementing, fixing, upgrading, or reviewing Filament panels, resources, forms, tables, actions, widgets, tenancy behavior, or admin UI interactions in Laravel.
---

# Laravel Filament

Start with [project context](../../references/project-context.md). Detect the
installed Filament, Livewire and relevant frontend versions. Inspect an existing
resource/page and follow its registration and namespace conventions. Read official
documentation for that major version before using component methods or hooks.

1. Define the user's task and the affected normal, empty, validation/error, and
   completion states. Change the smallest appropriate resource, page, action or
   widget. Do not mandate `app/Filament` when the project registers another layout.
2. Keep form/table/navigation configuration in Filament and delegate business
   workflows to owning actions, in Application when the design is layered.
   Do not create an action for a bare model update/create; use authorized,
   validated native CRUD for that case.
   Filament UI Actions configure interaction; business actions own workflows. Read
   [business write delegation](references/tenancy-and-actions.md#business-write-delegation)
   when designing or changing a write path; cover page, modal, relation and bulk
   paths that the feature exposes.
3. Enforce authorization on the server and scope both submitted related IDs and
   selectable records. Hidden buttons are presentation. Bulk, relation-manager,
   export and custom actions need the same intended access boundary. Read
   [tenancy and actions](references/tenancy-and-actions.md) when these apply.
4. Use responsive layouts, clear labels, translation placeholders, and consistent
   semantic colors. Read [UI and upgrades](references/ui-and-upgrades.md) for
   layout decisions, uploads, reactive behavior, or version migration. Choose
   layouts for the task; no universal sidebar ratio or ban on Grid is appropriate.
5. Test relevant component behavior and forged/unauthorized mutations using the
   installed testing APIs. Exercise changed interactions in a browser when
   available. A rendered screenshot alone does not prove saving, authorization,
   or asynchronous completion. Follow [testing](../testing/SKILL.md) and
   [verification](../../references/verification.md) for evidence boundaries.

For non-UI behavior, consult [implement](../implement/SKILL.md) only as needed.
For review-only requests, inspect these boundaries and report concrete defects
without rewriting the UI or introducing a new design system.
