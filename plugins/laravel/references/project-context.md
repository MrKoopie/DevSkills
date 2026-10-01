# Establish project context

Use this checklist at the first relevant task in a checkout. Reuse facts already
established in the conversation; refresh them when the checkout, dependencies,
test configuration, or task scope changes. This is preparation, not a separate
skill, background process, or required user interview.

1. Read the applicable project instructions and the user's acceptance criteria.
   Ask only about unresolved choices that materially affect the result. Respect
   an explicitly selected version or architecture.
2. Inspect `composer.json`, `composer.lock`, and representative nearby code. Use
   installed package metadata when available to distinguish installed from locked
   versions. Identify PHP, Laravel, and only the packages relevant to this task.
   For frontend work, inspect the package manager lockfile and build scripts.
3. Record existing namespaces, model placement, authorization and tenant entry
   points. Follow the application's conventions; folder names alone do not prove
   an architectural boundary. Inspect autoloading before moving classes.
4. Inspect actual test files, `tests/Pest.php` if present, PHPUnit configuration,
   Composer scripts, and CI. Mixed Pest/PHPUnit suites are valid. Determine which
   directories boot Laravel, how database isolation works, and which commands
   the repository requires. A dependency declaration alone does not establish
   the active runner or a usable test environment.
5. For package-specific syntax, use Context7 when available: resolve the library,
   then query documentation matching the installed major version. Otherwise use
   official versioned documentation or inspect the installed source. State an
   unresolved compatibility assumption; do not invent a method or silently
   upgrade a dependency to fit an example.

Scale discovery to the task. A translation-label change needs the nearby UI and
translation conventions, not a full architecture inventory. Report only facts
that affect the decision, plus any limitation that prevents verification.

For dependencies, prefer the project's compatible constraints and lockfile.
An upgrade request needs the target package's requirements and upgrade guide.
Composer `~3.0` allows versions below `4.0.0`; `~3.0.0` allows versions below
`3.1.0`. A constraint such as `^3.0` is a range, not an exact pin.

Source: [Composer constraints](https://getcomposer.org/doc/articles/versions.md).
