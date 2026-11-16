# Formatting and lint pilot

These are proposed settings to evaluate, not a globally installed configuration
or a claim that a project pilot passed. Preserve the project's preset, exclusions,
other finder settings and unrelated configuration/rules.
Confirm the installed Pint/PHP-CS-Fixer version supports the options, merge these
rules into a temporary copy of that configuration, and check a few representative
changed files before proposing a project-wide configuration change.

```json
{
  "rules": {
    "method_argument_space": {
      "on_multiline": "ensure_fully_multiline"
    },
    "blank_line_before_statement": {
      "statements": ["continue", "return", "try", "if", "foreach"]
    }
  }
}
```

The argument rule formats already-multiline signatures/calls; Pint does not
automatically wrap long expressions at a line-length target. Use roughly 120
characters as a guideline for manual wrapping under
[readable design](readable-design.md), not an extra linter or global gate.
The statement rule adds syntactic spacing before the selected statements; it
cannot detect meaningful groups of domain work. Check the effective preset first:
an option may already be active, and the sample statement list may
replace a broader existing list. Extend that effective list with the five
statements above rather than dropping existing entries such as `throw` or
`declare`. Preserve other options within either rule as well.

The existing `no_useless_else` proposal is separate from this whitespace pilot:
it removes redundant branches after an exit. Preserve its current project setting;
do not newly enable it solely for formatting or change control flow to shorten lines.

Use the repository's formatter check first. When authorized to pilot configuration,
use a temporary config and explicit file paths with the installed Pint command;
review the resulting scoped diff and run relevant checks. Report accepted settings,
actual formatting changes and any remaining manual readability decisions. Do not
introduce a whole-repository reformat as a side effect of a feature. Keep semantic
spacing, readable guards and method cohesion in review; do not invent Pint options
for cyclomatic complexity or method length. After formatting, inspect logical
grouping and long expressions yourself using the shared readable-design rules.
This pilot introduces no extra analyzer or project-wide line-length gate.

Official option references: [Pint configuration](https://laravel.com/docs/13.x/pint),
[method_argument_space](https://cs.symfony.com/doc/rules/function_notation/method_argument_space.html),
[blank_line_before_statement](https://cs.symfony.com/doc/rules/whitespace/blank_line_before_statement.html),
[no_useless_else](https://cs.symfony.com/doc/rules/control_structure/no_useless_else.html).
Check these against the installed versions rather than upgrading to match an example.
