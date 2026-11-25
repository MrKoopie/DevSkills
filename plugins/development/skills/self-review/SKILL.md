---
name: self-review
description: Use when the person or agent who built a change checks their own diff, functional coverage and test evidence before handing it to an independent technical reviewer.
---

# Review your own implementation

Read the pinned requirements, prototype and plan from the [local feature workspace](../../references/feature-workspace.md). Return those versions and the tested code identity with the self-review.

Perform this review as the builder. Start from the original request, confirmed
requirements (with IDs when available), project guidelines and the exact candidate you tested.

1. **Read the whole change as a caller.** Compare the branch with its intended
   base. Inspect the index, working tree and relevant untracked files, including
   new tests and configuration. Trace the public entry points touched by the
   change. Distinguish your work from pre-existing edits and consider their
   interaction where they affect the candidate.
2. **Reconcile intent and behavior.** For each requirement, point to the
   implementation and an observable result. Check that the actual assertion
   would detect a broken result. Inspect relevant negative cases and side
   effects. Identify accidental scope changes or an existing caller whose
   behavior silently changed.
3. **Check the project's rules against the actual code.** Apply the conventions
   that govern the touched area. Review ownership, readability and duplication
   in the end-to-end flow. For each remaining concern, name the file, the
   triggering condition and its effect on the requirement or caller.
4. **Fix and recheck.** Correct in-scope defects and missing coverage, reread the
   resulting diff and rerun checks affected by each fix. Record commands and
   observed results against the final tree. Carry forward a required check that
   could not run and explain the remaining uncertainty.
5. **Return the handoff.** Summarize the reviewed base, revision and local
   changes, functional coverage, corrections, test results and open findings.
   Label the result as the builder's self-review. In the feature workflow, send
   the candidate to [technical-review](../technical-review/SKILL.md) for a
   fresh review and its own verdict.
