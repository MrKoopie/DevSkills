# UI decisions and version changes

## Forms, tables, and feedback

1. Group fields by user task. A main column with a short metadata sidebar can
   help an edit screen; a single column often suits a short form. Choose spacing,
   width, columns and responsive breakpoints from actual content and established
   design. Verify keyboard order, narrow widths and long translated labels.
2. Choose live/deferred state updates intentionally. Reset stale dependent fields
   and validate the new relationship server-side. Avoid broad reactive queries
   that run on every keystroke without a user benefit.
3. Use consistent semantic colors with visible text, not color alone. Translate
   labels, validation messages and notifications using placeholders. For localized
   content, make the active locale, missing translation and fallback behavior clear.
4. Make table filters and bulk selection behavior apparent. Verify actual filter
   application and query performance. Use scoped counts and charts in widgets;
   hiding a widget is not a substitute for scoping its data.
5. Validate uploads, disk visibility, ownership and access to downloads. Keep
   private content private; changing a disk default is not a reason to make all
   uploads public. Treat stored rich text according to the application's HTML
   sanitization policy.
6. Success notifications follow actual outcomes. Queued work needs a queued or
   processing state and a way to observe completion/failure when the task requires
   it. Do not invent continuous monitoring for a one-time operation.

## Upgrades

Inspect the exact installed and requested target versions, their official upgrade
guides, and compatibility of third-party plugins, Livewire, PHP and build tooling.
Respect the selected target; do not request a newer major simply because it exists.

Apply only relevant documented changes: namespaces, Schema/Form method signatures,
action registration, utility injection, tenancy, upload visibility, filter defaults,
theme builds and test APIs. Automated upgrade tools do not prove custom components
or plugins work. Verify representative create/edit/view, relations, bulk actions,
uploads, policies and tenant switching after the change. Preserve requested scope
and report an incompatible plugin as a concrete blocker.

Sources: [Filament documentation](https://filamentphp.com/docs) and
[Livewire documentation](https://livewire.laravel.com/docs).
