---
name: pre-push-sync
description: Use before pushing work to a remote, including PR/MR creation and updates, when the target branch may have advanced.
---

# Pre-push sync

Integrate the latest target branch and adapt the work before pushing.

1. Identify the target remote and branch from the request, PR/MR base, or repository conventions. The feature branch's upstream is not necessarily the target. Ask only if ambiguous.
2. Preserve uncommitted work. Fetch the target remote; stop if fetching fails. Record the fetched target SHA and merge base with HEAD.
3. Inspect incoming commits and their diff from that merge base. Compare with our changes; trace effects through callers, contracts, dependencies, configuration, migrations, and tests. A conflict-free merge can still require adaptation.
4. Integrate the fetched target into the working branch using repository policy; otherwise merge. Resolve conflicts by preserving intent. Adopt incoming refactors and update affected code and tests. Restore preserved work and check it too. Never discard work or rewrite published history without authorization.
5. Run relevant tests and required checks on the combined result. Re-fetch immediately before the authorized push; if the target advanced, repeat inspection, integration, and validation. Stop on unresolved conflicts or failed checks.
6. Briefly report incoming changes, adaptations, and verification. Push only when already authorized; this skill grants no publishing permission.
