# Local feature history

At intake run `python3 <development-plugin>/scripts/start_feature.py <feature-slug> --repo <checkout>`.
Resume the existing feature when present. The command registers the work and audit
directories in Git's local info/exclude, verifies the effective exclusions and
preserves existing files. The local exclude file can be shared by linked worktrees. These rules are
repository-wide setup and persist even if a later feature-specific check fails.
On failure inspect the conflicting ignore rule before retrying. Remove shared
rules manually only after verifying other worktrees no longer rely on them.

Use one owning checkout and give every builder and reviewer the absolute feature
path. Keep files reachable if execution moves to another worktree. Before removing
an owning checkout, retain the directory and linked audit evidence in a durable
location, update references and verify them. Local ignored files have no Git backup.

| Path relative to the feature directory | Owner and content |
| --- | --- |
| README.md | Coordinator records the current confirmed combination, candidates, review status and next action. |
| requirements/vN.md | Original request, table with stable IDs, gaps, approval and associated prototype. |
| prototype/vN/ | Runnable demo, flow.mmd, entry point and scenario to try. |
| plans/vN.md | Independently reviewed plan pinning exact requirements and prototype; includes tests and per-file changes. |
| changes.md | Only requests from the user during implementation that depart from the agreed plan. Record date/source, request, IDs, original plan and resulting revisions. |
| validations/vN.md | Candidate base/head, dirty-tree manifest when relevant, pinned requirements/prototype/plan, expected prototype behavior versus observed product behavior per ID, checks, verdict, limitations and links to canonical audit evidence. |

Edit a draft in place. Freeze confirmed requirements/prototypes, reviewed plans and
finished validations. For a material revision create the next unused version of
the affected item. At the top record its predecessor, reason, affected IDs and
needed rechecks (use a small README in the prototype folder). Show the full
requirements table after changes. Advance the index only after the corresponding
confirmation or review. On rollback select a compatible prior combination and
record the reason in the index. A historical pass belongs to its tested code.
Record a new validation for a different candidate. Keep findings, technical
plan refinements and test reruns out of changes.md.

## Superpowers

Route brainstorming's specification to the requirements version, with the
confirmed prototype alongside it. Route writing-plans to the plan version.
Give inline and delegated executors the pinned absolute paths and actual code
worktree. In this local-only flow use `execution/plan-vN/` inside the feature
directory for progress.md, task briefs and review packages. Preserve the
Superpowers task/review sequence and ledger identity. Write the briefs and
review packages here directly when installed helpers mandate their own
workspace or generate a .gitignore. Preserve technical decisions in progress.md,
material revisions in the next plan and evidence in validations/. Keep the
feature history through external acceptance and any worktree cleanup.

The independent validator still fetches its original issue or confirmed brief,
runs its independent review and produces its canonical report and evidence.
Supply the pinned prototype for comparison, inspect/run its scenarios against
the candidate and reference the evidence in the validation version. Record
unexercised paths explicitly; a reference alone does not prove equivalence.
