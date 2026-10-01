# Artifact contract

## Scope, names and ownership

Write rewritten code, identifiers, comments, tests and documentation in English.
Keep supported user-facing languages in translation resources. Translate internal
names through explicit data/API compatibility handling; do not silently rename
provider fields or historical data. Screenshots show the actual UI language.

Task/item IDs follow `^[FSTDIR][0-9]{3,}-[A-Z0-9]+(-[A-Z0-9]+){0,3}$`:
F flow, S state, T technical path, D dependency, I improvement/defect correction,
R rewrite slice. Use tight purpose slugs, e.g. `F001-ADD-USERS`. Allocate unique
numbers per prefix; state numbers are local to a flow. Outside its flow, qualify
`F001-ADD-USERS--S001-INVALID-INPUT`. Never recycle IDs; change labels separately.
Use full IDs in filenames, test metadata/descriptions, diagrams and handoffs, not
as programming identifiers. Preserve original tracker IDs as source references.

The parent alone edits the index, coverage, criteria, slice plan and consolidated
comparisons. Delegates own disjoint record paths and return rows for reconciliation.

## Local evidence

Resolve the target Git root. Before creating evidence, ensure its root `.gitignore`
contains `/.ai/triage/`, preserve existing rules and verify from that root:

```sh
git check-ignore -q --no-index -- .ai/triage/ignore-probe.md
```

Before any associated commit, run the discovered `feedback-triage` plugin's
`scripts/check_validation_artifacts.py --repo <target-root>`. Resolve that plugin
through the available skill catalog; do not assume a sibling installation path.
If unavailable, inspect `git ls-files -z -- .ai/triage` from the target root; any
indexed evidence path blocks the commit. This catches staged and already tracked
files. Remove offending artifacts from the index while retaining local copies.
Do not commit reports/screenshots; reusable executable tests belong in normal suites.

```text
.ai/triage/modernize/
  index.md
  coverage.md
  criteria/I001-FIX-ROUNDING.md
  slices/R001-REWRITE-USERS.md
  baseline/<snapshot>/
    manifest.json
    flows/F001-ADD-USERS.md
    technical/T001-SEND-INVITES.md
    dependencies.md
    visuals/F001-ADD-USERS--S001-INVALID-INPUT--DESKTOP.png
    diagrams/F001-ADD-USERS.mmd
  candidate/<snapshot>/...
  comparison/<baseline>--<candidate>.md
```

## Replayable snapshots and coverage

The manifest records source identity; each snapshot's repository and full base/head
SHAs; dirty paths/status/content hashes; capture time; running-app revision; relevant
runtime/lockfile versions; locale/timezone/viewport; synthetic fixture identity/hashes;
product/test/adapter recovery references; isolated run/test instructions; proof mode.
Retain retrievable revisions or recoverable local snapshots of uncommitted material.
Hashes alone cannot recreate files. Never copy secrets or personal/confidential data
into reports or snapshot archives; reference protected local configuration by name.
If a revision is unknown, say so. Recheck source/product identity after capture and
before a verdict; refresh affected evidence on drift. Freeze baselines, create new
candidate snapshots, and keep both replayable even across different repositories.

Coverage rows: source inventory entry → actor/entry point → capability/state/branch
ID → requirement/criterion → test/evidence link → proof status. Status is `observed`,
`tested`, `source-only`, `blocked` or `unknown`, not a verdict. Exclusions have reasons.
Report mapped/excluded/unmapped counts per inventory, including technical operations.
Keep the index about 250–400 words and records about one screen; these are targets,
not reasons to omit branches or uncertainty. Store shared facts once and link them.
