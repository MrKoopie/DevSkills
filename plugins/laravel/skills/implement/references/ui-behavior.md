# Livewire and Blade behavior

1. Detect the installed Livewire version and existing component style. Verify
   lifecycle hooks, binding modifiers and event APIs against that version.
2. Treat public state and action parameters as untrusted. Authorize on the server
   at mutation time, scope model lookup, and validate dependent selections again
   before saving. A disabled button or locked-looking UI is not authorization.
3. Keep request/render state in the component and reusable business operations in
   the owning module. Share invariant checks with other entry points rather than
   duplicating UI-only guards. Avoid queries in repeatedly evaluated display
   methods when eager loading or an appropriate computed value suffices.
4. Preserve localization and accessible labels. Use translation placeholders for
   dynamic values. Blade output is escaped by default; sanitize deliberately
   supported rich HTML rather than rendering arbitrary input unescaped.
5. Verify loading, validation failure, empty state, successful completion and
   duplicate clicks when relevant. Success feedback follows a confirmed outcome;
   dispatched work should be described as queued, not completed. Preserve input
   after recoverable errors and reset stale dependent fields intentionally.
6. Use component tests for state/authorization and browser checks for changed
   interactions, focus, responsive layout, and JavaScript behavior. Report missing
   browser access as an evidence limitation, not a reason to fabricate proof.

Source: [Livewire documentation](https://livewire.laravel.com/docs).
