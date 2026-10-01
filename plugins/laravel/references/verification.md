# Verify the requested outcome

Use during implementation completion or a requested review. This reference
absorbs the useful developer/reviewer procedures without requiring an agent,
external review service, particular model, or additional plugin.

1. Compare the change with the original request and existing contract. Cover a
   normal case, the relevant denied/invalid case, and a state or failure boundary
   where the change introduces one. Derive criteria from the supplied task and
   existing behavior before asking for more information.
2. Inspect callers and side effects affected by the change: authorization, tenant
   scope, persistence, jobs, events, external requests, and user-visible output.
   Distinguish a confirmed defect from a style preference or speculative risk.
3. Run the repository's applicable tests, formatter and static analysis commands.
   Reuse existing checks and configuration. For behavior fixes, show a regression
   failing for the relevant reason before the fix and passing after it when the
   environment permits. For structural changes, establish and preserve the
   existing behavior baseline. Do not add tests for a label edit or tests that
   merely assert class names or directory layout.
4. Exercise UI interactions when they change. Report browser proof separately
   from component tests, and provider sandbox proof separately from HTTP fakes.
   A mock cannot establish the remote provider's behavior. An unavailable check
   remains unverified, even when other checks pass.
5. In review-only mode, report actionable findings with file/line evidence,
   triggering conditions, consequence, and the smallest appropriate correction.
   Do not implement findings unless the task authorizes fixes. In implementation
   mode, correct verified in-scope findings and rerun the affected checks.

The final result should identify what changed, what evidence supports it, and
what remains unverified. Update documentation when the change alters setup,
public contracts, or normal developer/user workflows. Do not generate documents
for every internal edit. Run review directly using these steps; no delegation
or independent-review claim is implied. Do not create a PR, merge, deploy, or
contact someone merely because verification completed.
