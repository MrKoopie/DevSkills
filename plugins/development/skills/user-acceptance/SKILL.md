---
name: user-acceptance
description: Prepare an external user's acceptance test for a reviewed candidate and record the user's actual decision against the agreed functional changes.
---

# External user acceptance

Use the confirmed prototype and exact candidate recorded in the [local feature workspace](../../references/feature-workspace.md). Preserve prior verdicts and record the user’s decision in a validation version for this combination.

1. Identify the candidate revision and the environment where the user can
   exercise it. Check which revision that environment serves. Check that technical review, functional/UX validation, CodeRabbit review and
   human code review cover the candidate and the agreed requirements. Use
   requirement IDs to trace coverage where available. If evidence is missing,
   stale or has unresolved blockers, identify the pending check. You may prepare
   scenarios while it is pending. Hold the external test invitation until the
   candidate and all required review outcomes match.
2. Write a short handoff in the user's language. For each agreed outcome give
   the starting state or role, realistic actions and a visible expected result.
   Include error and recovery paths when they are part of the agreed behavior.
   Use data suitable for the named environment. Ask the user to record what
   happened, which scenario they tried and whether they accept that revision.
3. Provide the handoff to the requester. Contact an external recipient only
   when authorized. Mark the result **awaiting user validation** until the
   external user actually responds. Developer testing and peer approvals can
   accompany the handoff as supporting evidence.
4. Record the tester, date, revision/environment, scenarios exercised, observed
   differences and explicit decision. For a partial run, list what remains.
   Mark accepted only when all four review outcomes cover this candidate and
   the user explicitly accepts the agreed scope on that version. Record feedback
   received before those checks finish as observations and obtain the user's
   decision once the candidate is ready. For a rejected outcome, send the observation and expected
   result back for correction. Take a changed requirement back to planning.
   After a fix, recheck affected tests and reviews, verify the replacement
   candidate and ask the user to retry affected scenarios. Preserve the earlier
   decision alongside the new result.
