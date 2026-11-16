# Shared review questions

Apply relevant questions across the full user action, including subsequent refresh
and failure handling. Record a demonstrated problem, smallest correction and the
behavior that must remain. Separate defects, readability improvements and open
questions. These are prompts for investigation; a finding needs a concrete
scenario, consequence and supporting evidence. Shared design decisions live in
[readable design](readable-design.md).

## General review questions

Architecture, implementation and review use this single shared set; do not copy
it into individual skills or reports as a second checklist.

1. **Simplicity:** Does the change solve the concrete problem without unnecessary
   layers or mechanisms?
2. **Responsibility:** Does each component have a clear purpose, with cohesive
   steps kept together?
3. **Duplication:** Can existing data or logic be reused without hidden
   dependencies or stale information?
4. **Contracts:** Are inputs, outputs, preconditions and responsibilities
   unambiguous?
5. **Readability:** Do names, structure and formatting explain the intent without
   unnecessary helpers or abstractions?
6. **Correctness:** Are existing guarantees preserved, including relevant edge
   cases and partial failures?
7. **Error handling:** Are failures handled at the appropriate boundary, while
   unexpected errors remain visible?
8. **Truthful results:** Do returned results and messages reflect what actually
   happened?
9. **Verification:** Do tests exercise required behavior and relevant failure
   cases rather than merely the chosen implementation?
10. **Scope and justification:** Does the solution follow the agreed requirements,
    with added complexity and assumptions justified by evidence?

When assessing protection or recovery mechanisms, apply the focused questions in
[readable design](readable-design.md#match-protection-and-recovery-to-agreed-needs)
at that decision point rather than maintaining another copy here.

## Supplemental CodeRabbit-derived checks

These are a limited review sample, not an exhaustive bot audit. Validate every claim against the actual contract and installed versions.

- Is the concurrency decision based on the required current locking read rather
  than a stale snapshot?
- Are only explicitly validated/authorized fields persisted?
- Are missing, empty, unchecked and fallback values distinguished correctly?
- Does pagination have a stable, unique ordering when primary sort values tie?
- Does an analyzer/tool claim hold for the installed version and effective config?
- Does a price change respect the agreed supersession rule? A withdrawn review
  claim is a warning to verify the contract, not a rule to change prices.

## Source trail

The strict query boundary, proportional architecture check for every refactor and
formatting pilot are user-approved design choices. They are included in the
working guidance even where broader practical validation is still pending.

Supplemental source examples: [locking](https://gitlab.com/eyecare-group/goldeneye/-/merge_requests/437#note_3928790876),
[value distinctions](https://gitlab.com/eyecare-group/goldeneye/-/merge_requests/448#note_3962263071),
[tool configuration](https://gitlab.com/eyecare-group/goldeneye/-/merge_requests/448#note_4015511985),
[withdrawn price claim](https://gitlab.com/eyecare-group/goldeneye/-/merge_requests/437#note_3929442880).
The supplied synthesis also identified validated-field and pagination checks; no
individual note URL was supplied for those two, so do not invent one or claim
independent revalidation of every source discussion.
