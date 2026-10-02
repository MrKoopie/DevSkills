# Install DevSkills

Install **v0.2.0** from the [published version](https://github.com/MrKoopie/DevSkills/tree/v0.2.0).
You need Git and the client you want to use. Choose the plugins you need;
App Modernization also needs Feedback Triage for its independent final audit.

| Client | Available plugins | Catalog or extension |
| --- | --- | --- |
| Codex App and CLI | Git Workflow, Laravel, App Modernization, Feedback Triage | [Codex catalog](.agents/plugins/marketplace.json) |
| Claude Code | Git Workflow, Laravel, App Modernization, Feedback Triage | [Claude catalog](.claude-plugin/marketplace.json) |
| Cursor | Feedback Triage | [Cursor catalog](.cursor-plugin/marketplace.json) |
| Factory Droid | Feedback Triage | [Factory catalog](.factory-plugin/marketplace.json) |
| GitHub Copilot CLI | Feedback Triage | [Copilot catalog](.github/plugin/marketplace.json) |
| Kimi Code | Feedback Triage | [Kimi catalog](kimi-marketplace.json) |
| Gemini CLI | Feedback Triage | [Extension manifest](plugins/feedback-triage/gemini-extension.json) |

## Codex App and CLI

Register this version's Git marketplace, then install the plugins you need:

```sh
codex plugin marketplace add MrKoopie/DevSkills --ref v0.2.0
codex plugin add feedback-triage@devskills
codex plugin add laravel@devskills
codex plugin add app-modernization@devskills
codex plugin add git-workflow@devskills
codex plugin list --marketplace devskills
```

For the desktop app, restart it, open the Plugins Directory, select DevSkills
and install the desired plugins. Start a new chat to load installed skills.
The Git marketplace is pinned to this version; refreshing it retains that pin.
See the [Codex plugin documentation](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli).

## Claude Code

Register the tagged marketplace and install the plugins you need:

```sh
claude plugin marketplace add 'MrKoopie/DevSkills#v0.2.0'
claude plugin install feedback-triage@devskills
claude plugin install laravel@devskills
claude plugin install app-modernization@devskills
claude plugin install git-workflow@devskills
```

Open `/plugin` in Claude Code to check the installed plugins. Start a new
session, then invoke a skill such as `/laravel:architecture` or
`/feedback-triage:process-pr-feedback`.
See the [Claude plugin installation guide](https://code.claude.com/docs/en/plugins/install).

## Checkout for local installation

Factory Droid, Copilot CLI, Kimi Code and Gemini CLI use the released checkout
in the following sections. Clone it once and run their terminal commands
from the resulting DevSkills directory:

```sh
git clone --depth 1 --branch v0.2.0 https://github.com/MrKoopie/DevSkills.git DevSkills
cd DevSkills
git describe --tags --exact-match
```

The last command should print `v0.2.0`. Keep this directory in place
when a client registers it as a local marketplace.

## Cursor

1. Open **Customize** and select **From GitHub Repository**.
2. Enter `https://github.com/MrKoopie/DevSkills` and import its plugin marketplace.
3. Install Feedback Triage and confirm its skills appear in Customize.

Use the published `main` branch for this import. It contains the latest snapshot;
the CLI examples instead pin the version shown above. See the
[Cursor installation documentation](https://cursor.com/docs/skills#installing-skills-from-a-repository).

## Factory Droid

From the released checkout:

```sh
droid plugin marketplace add .
droid plugin marketplace list
```

Copy the exact registered name shown for this checkout, including capitalization.
Factory derives it from the source, so it may differ from the catalog's
`devskills` name. Enter that registered name when the following command prompts:

```sh
printf 'Registered marketplace name: '
read -r marketplace_name
droid plugin install "feedback-triage@$marketplace_name"
droid plugin list
```

Start a new Droid session to load the plugin. See the
[Factory plugin documentation](https://docs.factory.com/harness/plugins).

## GitHub Copilot CLI

From the released checkout:

```sh
copilot plugin marketplace add .
copilot plugin install feedback-triage@devskills
copilot plugin list
```

Start a new Copilot session and check the installed plugin. See the
[Copilot plugin installation guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-finding-installing).

## Kimi Code

Start `kimi` from the released checkout. In its TUI, run:

```text
/plugins install ./plugins/feedback-triage
/plugins list
/reload
```

You can also browse the packaged catalog with
`/plugins marketplace ./kimi-marketplace.json`. Kimi copies a local plugin
into its managed directory; reinstall it to pick up a different version.
See the [Kimi plugin documentation](https://moonshotai.github.io/kimi-code/en/customization/plugins.html).

## Gemini CLI

From the released checkout, install the extension's own directory:

```sh
gemini extensions install ./plugins/feedback-triage
gemini extensions list
```

Start a new Gemini session to load its skills and agents. The extension manifest
is inside `plugins/feedback-triage`, so use that directory for installation.
See the [Gemini extension reference](https://geminicli.com/docs/extensions/reference/).

## Change versions and troubleshoot

1. For another release, use that version's installation guide, register its tag
   or checkout, and reinstall or update the plugins in your client's manager.
2. If a plugin command is unavailable, check your client's version and its
   linked installation documentation. The catalogs above show which plugins
   each client can discover.
3. If installation succeeds but skills are missing, check the client's
   installed-plugin list and start a fresh session. Use `/reload` in Kimi.
