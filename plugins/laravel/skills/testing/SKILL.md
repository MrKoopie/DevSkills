---
name: testing
description: Use when creating, repairing, or reviewing Laravel Pest or PHPUnit tests, assessing regression coverage, or verifying application behavior against acceptance criteria.
---

# Laravel testing

A useful test fails when the required behavior is violated. Start with
[project context](../../references/project-context.md) and the supplied request.
Inspect the nearest existing tests and actual runner configuration before choosing
syntax, directories, or commands. Preserve Pest, PHPUnit, or a mixed suite.

## Build the evidence

1. Map the task's acceptance criteria to observable outcomes and relevant negative
   cases. If criteria are implicit, derive them from the task and established
   behavior; ask only about a material ambiguity. Avoid tests copied solely from
   the implementation, framework behavior, or a coverage percentage target.
2. Choose the layer that exercises the risk. Pure calculations can be unit tests.
   Models/actions using the container, factories, or database need Laravel's
   TestCase and isolated persistence, regardless of their directory name.
3. For a new behavior or bug fix, run a focused test before implementation and
   verify the failure is the intended missing behavior. Missing autoloading,
   database access, or a fixture is a setup failure. For refactoring, capture and
   preserve the existing behavior rather than manufacturing a failing test.
4. Use factories and normal framework execution for application behavior. Fake
   external effects at their boundary. Test the dispatch contract separately
   from job execution; `Queue::fake()` does not prove a job's `handle()` works.
5. Follow [test boundaries](references/test-boundaries.md) for authentication,
   tenants, database state, providers, and browser checks. Do not call an invented
   helper merely because it appeared in an example.
6. Run the focused tests and applicable repository gates. Stop broadening tests
   once the relevant risk and required checks are covered. Report failures,
   skips, and unavailable environments accurately using
   [verification](../../references/verification.md).

## Review coverage

For each important requirement, identify the assertion and a plausible change
that would violate it. When useful, temporarily introduce that defect in an
isolated fixture and confirm the test detects it. Do not claim mutation testing
from a conceptual inspection. State uncovered behavior precisely, including
authorization, duplicate delivery, and side effects that are only mocked.

This skill performs testing and coverage review directly. It does not require
an agent, a test-framework migration, a PR, or access to a live provider.
