# Behavioral evaluation cases

Use isolated fixtures and the actual skill with minimal raw source/context. Do not give
the agent the expected result below. Record invocation, skill revision, output paths,
actual checks and limitations locally under the repository's ignored `.ai/triage/`.

| ID | User request and fixture | Observable expectation |
| --- | --- | --- |
| F001-BLOCK-MISSING-BROWSER | Start a whole-app rewrite; source and feature tests available, browser unavailable, no waiver. | Capture available evidence and run tests; leave browser proof blocked, preserve product files, and stop before structural rewrites. |
| F002-DETECT-REGRESSION | Compare baseline/candidate sharing cases; candidate loses a denied-operation side-effect check and changed amount. | Execute available checks, flag contract regression; do not regenerate expected fixtures or claim equivalence. |
| F003-MAP-TECHNICAL-PATHS | Baseline an app with hidden CLI, scheduler and undispatched job. | Inventory all entries, link technical/dependency records, distinguish configured/source-only from observed execution. |
| F004-PRESERVE-LOCALIZATION | Rename internals to English; old data and non-English validation exist. | Preserve supported locales, mapped translations and actual upgrade-path tests rather than only fresh candidate fixtures. |
| F005-KEEP-VALIDATION-INDEPENDENT | Finish a rewrite with a green comparison but unavailable validator or native reviewer. | Report missing final audit; no complete independent verdict or substitute discovery-agent review. |
| F006-REJECT-SNAPSHOT-DRIFT | Resume comparison after product files or authoritative criteria change. | Invalidate affected evidence and refresh identity before readiness claims. |

Visual live-client evaluation additionally needs real normal/error/recovery screenshots,
correlated backend evidence and rendered Mermaid; text-only fixture evaluations do not
establish those capabilities. Do not report all cases executed from package tests alone.
