# UX

[UX Basics](skills/ux-basics/SKILL.md) covers spacing by relationship, visual grouping,
alignment, readable text, action hierarchy, and responsive sizing. Reuse the app's
design system; the sample values are starting points rather than a required theme.

1. Invoke `ux-basics` with a screenshot or an existing UI to adjust.
2. Open [the Mailing lists before/after example](skills/ux-basics/examples/mailing-list-spacing.html)
   in a browser. Switch layouts and enable long content to see how the grouping works.
3. Check the changed UI at desktop and narrow widths, with long content and enlarged
   text. The skill requires honest reporting when browser verification is unavailable.

The example is a layout illustration. Its Create, Edit, Delete, and Close controls
do not perform application actions. It is not a production modal component.

Codex and Claude use the same skill source. The package has no runtime dependencies,
agents, hooks, or external services. Catalog registration prepares distribution;
it does not install or publish the plugin. See [validation scenarios](tests/scenarios.md).
