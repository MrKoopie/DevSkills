# Install DevSkills

Run these commands from the root of the DevSkills checkout you want to install.
Keep that directory in place when a client registers it as a local marketplace.
For the published `v0.4.0` release, use its [installation guide](https://github.com/MrKoopie/DevSkills/blob/v0.4.0/INSTALL.md).

The full Development workflow uses Git Workflow for PR/MR feedback.
App Modernization uses Development for its independent final audit.
Git Workflow's background PR/MR watch requires Codex on a Unix host.

| Client | Available plugins | Catalog or extension |
| --- | --- | --- |
| Codex App and CLI | Development, Git Workflow, UX, Laravel, App Modernization | [Codex catalog](.agents/plugins/marketplace.json) |
| Claude Code | Development, Git Workflow, UX, Laravel, App Modernization | [Claude catalog](.claude-plugin/marketplace.json) |
| Cursor | Development, Git Workflow | [Cursor catalog](.cursor-plugin/marketplace.json) |
| Factory Droid | Development, Git Workflow | [Factory catalog](.factory-plugin/marketplace.json) |
| GitHub Copilot CLI | Development, Git Workflow | [Copilot catalog](.github/plugin/marketplace.json) |
| Kimi Code | Development, Git Workflow | [Kimi catalog](kimi-marketplace.json) |
| Gemini CLI | Development, Git Workflow | [Development](plugins/development/gemini-extension.json) and [Git Workflow](plugins/git-workflow/gemini-extension.json) |

## Codex App and CLI

Register the local marketplace, then install the plugins you need:

```sh
codex plugin marketplace add "$PWD"
codex plugin add development@devskills
codex plugin add laravel@devskills
codex plugin add app-modernization@devskills
codex plugin add git-workflow@devskills
codex plugin add ux@devskills
codex plugin list --marketplace devskills
```

For the desktop app, restart it, open the Plugins Directory, select DevSkills
and install the desired plugins. Start a new chat to load installed skills.
See the [Codex plugin documentation](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli).

## Claude Code

Register the local marketplace and install the plugins you need:

```sh
claude plugin marketplace add "$PWD"
claude plugin install development@devskills
claude plugin install laravel@devskills
claude plugin install app-modernization@devskills
claude plugin install git-workflow@devskills
claude plugin install ux@devskills
```

Open `/plugin` in Claude Code to check the installed plugins. Start a new
session, then invoke a skill such as `/laravel:architecture` or
`/git-workflow:process-pr-feedback`.
See the [Claude plugin installation guide](https://code.claude.com/docs/en/plugins/install).

## Cursor

1. Open **Customize** and select **From GitHub Repository**.
2. Enter `https://github.com/MrKoopie/DevSkills` and import its plugin marketplace.
3. Install Development and Git Workflow and confirm their skills appear in Customize.

This import uses the published `main` branch. See the
[Cursor installation documentation](https://cursor.com/docs/skills#installing-skills-from-a-repository).

## Factory Droid

From the local checkout:

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
droid plugin install "development@$marketplace_name"
droid plugin install "git-workflow@$marketplace_name"
droid plugin list
```

Start a new Droid session to load the plugin. See the
[Factory plugin documentation](https://docs.factory.com/harness/plugins).

## GitHub Copilot CLI

From the local checkout:

```sh
copilot plugin marketplace add .
copilot plugin install development@devskills
copilot plugin install git-workflow@devskills
copilot plugin list
```

Start a new Copilot session and check the installed plugin. See the
[Copilot plugin installation guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-finding-installing).

## Kimi Code

Start `kimi` from the local checkout. In its TUI, run:

```text
/plugins install ./plugins/development
/plugins install ./plugins/git-workflow
/plugins list
/reload
```

You can also browse the packaged catalog with
`/plugins marketplace ./kimi-marketplace.json`. Kimi copies a local plugin
into its managed directory; reinstall it to pick up a different version.
See the [Kimi plugin documentation](https://moonshotai.github.io/kimi-code/en/customization/plugins.html).

## Gemini CLI

From the local checkout, install each extension from its own directory:

```sh
gemini extensions install ./plugins/development
gemini extensions install ./plugins/git-workflow
gemini extensions list
```

Start a new Gemini session to load its skills and agents. Each plugin directory contains its own extension manifest.
See the [Gemini extension reference](https://geminicli.com/docs/extensions/reference/).

## Change versions and troubleshoot

1. For another release, use that version's installation guide, register its tag
   or checkout, and reinstall or update the plugins in your client's manager.
2. If a plugin command is unavailable, check your client's version and its
   linked installation documentation. The catalogs above show which plugins
   each client can discover.
3. If installation succeeds but skills are missing, check the client's
   installed-plugin list and start a fresh session. Use `/reload` in Kimi.
