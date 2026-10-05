# sdlc-pipeline

A Claude Code plugin that turns a **business use case** into reviewed, tested and archived code
through a team of specialised agents, with two human approval gates. Every run leaves a
retrospective and a session report behind, so you can see what it did and improve it.

```
use case ─▶ architect ─▶ spec-reviewer ─▶ 🚦 GATE 1 ─▶ junior-dev ─▶ qa ─▶ senior-dev ─▶ 🚦 GATE 2 ─▶ archive ─▶ 📝 retro
            (plan)       (plan gate)      (you)        (implement)  (verify) (code review)  (you)
```

The planning and bookkeeping run on [OpenSpec](https://github.com/Fission-AI/OpenSpec). The plugin
doesn't assume a stack: the agents bring the roles and the judgment, and each project brings its own
stack rules in a short **profile** file (`.claude/sdlc-profile.md`).

## Contents

| Component | Name | What it does |
|-----------|------|--------------|
| Skill | `/sdlc-pipeline:init` | Sets a project up: checks OpenSpec, writes the profile, creates the folders. |
| Skill | `/sdlc-pipeline:write-domain` | Drafts `domain/` from your code and docs, then interviews you to confirm it and fill the gaps. |
| Skill | `/sdlc-pipeline:write-standards` | Builds `standards/` from a catalogue of architecture and concern rules you keep, adapt or drop, and updates the profile to cite them. |
| Skill | `/sdlc-pipeline:write-use-case <idea>` | Interactively drafts a business use case from the domain docs and saves it to `use-cases/`. |
| Skill | `/sdlc-pipeline:build-use-case <path>` | Runs the whole pipeline for one use case, with the two gates, fix loops, budget caps and the retrospective. |
| Skill | `session-report` | Turns a session log into an HTML report (agent timeline, gate value, errors, context use). Ask *"analyse this session"*. |
| Agent | `architect` | Use case → OpenSpec change (proposal, design, spec delta, tasks). |
| Agent | `spec-reviewer` | Read-only plan gate: standards conformance + design soundness. |
| Agent | `junior-dev` | Implements `tasks.md` and stays inside the plan. |
| Agent | `qa` | Checks every requirement has a test, runs the suite, reports evidence. |
| Agent | `senior-dev` | Final code review; fixes what it finds and hands design calls back. |
| Agent | `use-case-writer` | One-shot use-case drafting (the non-interactive `write-use-case`). |
| Hooks | `hooks/hooks.json` | Logs every tool call and agent event to `logs/pipeline-events.jsonl` in the project. |
| Script | `scripts/pipeline-report.py` | Renders that event log as an HTML dashboard. |
| Templates | `templates/` | Profile, use case, retrospective, retrospectives README, and the standards catalogue (`templates/standards/`). |

Agents show up namespaced, for example `sdlc-pipeline:architect` in `/agents`, and you can run one
by itself: *"Use the sdlc-pipeline:qa agent to verify add-product-search"*.

## Prerequisites

- [Claude Code](https://code.claude.com) with plugin support.
- The **OpenSpec CLI** (`npm install -g @fission-ai/openspec`), initialised in the project
  (`openspec init`), so that `openspec/config.yaml` and the `opsx:*` / `openspec-*` skills exist.
- **Python 3.8+** for the hooks and reports (standard library only).
- Recommended: Matt Pocock's [skills plugin](https://github.com/mattpocock/skills)
  (`/plugin install mattpocock-skills@claude-plugins-official`) for the `grill-me` skill, which
  you use to write the PRD.
- Recommended: a PRD, a `domain/` and a `standards/` folder. See [Quick start](#quick-start) and
  [Domain and standards](#domain-and-standards).

## Domain and standards

The profile tells the agents your stack. Two folders in your project tell them the rest:

- **`domain/`** describes the business: `overview.md`, `glossary.md`, `business-rules.md`,
  `bounded-contexts.md` and `actors-and-personas.md`. The use-case writer, architect and
  spec-reviewer read it, so use cases and plans use your terms, honour your rules and stay inside
  the right bounded context. Business language only, no implementation.
- **`standards/`** holds the rules your team builds by, one file per concern (for example
  `architecture.md`, `testing.md`). Keep each rule checkable and numbered. The profile cites them;
  the developers follow them and every reviewer finding cites the rule it breaks
  (`standards/testing.md §3`).

Without them the pipeline still runs, but its plans are only as good as the use case. Write a PRD
with `grill-me` first; it gives the domain docs their words. Then run `/sdlc-pipeline:write-domain`,
which drafts the domain docs from the PRD, your code and your docs and interviews you for the rest.
Then run `/sdlc-pipeline:write-standards`: pick an architecture and the concerns you care about,
keep, adapt or drop each ready-made rule, and it updates the profile to cite the rules you kept.
When both exist, update `openspec/config.yaml` to point at them and check the README is accurate.
They grow from there: `write-use-case` flags domain gaps, the architect adds tasks to record new
terms and rules, and retrospectives recommend new or clearer standards.

[docs/domain-and-standards.md](docs/domain-and-standards.md) covers what each file should contain,
with examples, how the two skills build them, sample prompts for drafting them by hand, and how to tell which docs earn their place.

## Install

**For a team (recommended):** add this to the project's checked-in `.claude/settings.json`. Teammates
who trust the folder are asked to install the plugin the first time they open it.

```json
{
  "extraKnownMarketplaces": {
    "sdlc-pipeline": { "source": { "source": "github", "repo": "prule/sdlc-pipeline" } }
  },
  "enabledPlugins": { "sdlc-pipeline@sdlc-pipeline": true }
}
```

**Just for you:**

```
/plugin marketplace add prule/sdlc-pipeline
/plugin install sdlc-pipeline@sdlc-pipeline
```

### Recommended project settings

Plugins can't set environment variables or permissions, so put these guardrails in the project's
`.claude/settings.json` yourself:

```json
{
  "env": {
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "16000",
    "MAX_THINKING_TOKENS": "12000",
    "BASH_DEFAULT_TIMEOUT_MS": "180000",
    "BASH_MAX_TIMEOUT_MS": "600000"
  },
  "permissions": {
    "defaultMode": "acceptEdits",
    "deny": ["Bash(<your publish/deploy command>:*)"]
  }
}
```

## Quick start

Set a project up in this order. [docs/getting-started.md](docs/getting-started.md) covers each step.

1. **Write a PRD.** Run `/mattpocock-skills:grill-me` on your product idea. It interviews you until
   every decision is settled. Then ask it to write the result to `docs/prd.md`.
2. **Set up the project.** Run `openspec init`, then `/sdlc-pipeline:init` for the profile and
   folders.
3. **Document the domain.** Run `/sdlc-pipeline:write-domain`. It drafts `domain/` from the PRD and
   your code, then asks you what it couldn't find.
4. **Choose the standards.** Run `/sdlc-pipeline:write-standards`. It writes `standards/` and
   updates the profile to cite them.
5. **Update the OpenSpec config and the README.** Point `openspec/config.yaml`'s `context` and
   `rules` at the PRD, `domain/` and `standards/`, and make sure `README.md` describes the product
   and its commands accurately. No skill does this for you.
6. **Write and build use cases:**

```
/sdlc-pipeline:write-use-case <rough idea>            # draft use-cases/UC-<n>-<slug>.md, then review it
/sdlc-pipeline:build-use-case use-cases/UC-003-….md   # run the pipeline; answer the two gates
```

`build-use-case` creates a `feat/uc-<n>-<slug>` branch from your base branch (as the profile says),
runs the agents, stops for your approval at Gate 1 (the plan) and Gate 2 (the finished change), then
writes `retrospectives/<date>-<change>.md`, `reports/sessions/<session>.report.html` and the run's
data beside it, `<session>.summary.json`. Commit all three with the change and open the PR.

## Documentation

- **[docs/getting-started.md](docs/getting-started.md)**: setting a project up, in order: PRD,
  init, domain, standards, then the OpenSpec config and README.
- **[docs/pipeline.md](docs/pipeline.md)**: the stages, gates, fix loops, budget guardrails and
  retrospectives, and how to run any phase by hand.
- **[docs/profile.md](docs/profile.md)**: the project profile, field by field, with a worked example.
- **[docs/domain-and-standards.md](docs/domain-and-standards.md)**: what goes in `domain/` and
  `standards/`, how the agents use them, and how to create them.
- **[docs/observability.md](docs/observability.md)**: the event-log hooks, the pipeline dashboard
  and session reports.
- **[docs/evaluating-the-pipeline.md](docs/evaluating-the-pipeline.md)**: how to tell whether the
  pipeline, and each agent and doc in it, is earning its place, including A/B ablations.
- **[skills/session-report/README.md](skills/session-report/README.md)**: the report generator in
  full.
- **[CHANGELOG.md](CHANGELOG.md)**.

## Updating

Claude Code checks the marketplace for a new `version` and updates the plugin. To update now, run
`/plugin marketplace update sdlc-pipeline`, then restart Claude Code. Project-owned files (the
profile, use cases, retrospectives) are never touched by an update. Read the CHANGELOG for anything
that asks you to change the profile.

## Developing the plugin

```bash
git clone https://github.com/prule/sdlc-pipeline ~/projects/sdlc-pipeline
cd <a project that uses it>
claude --plugin-dir ~/projects/sdlc-pipeline    # this session uses your working copy
```

Changes to agents, skills and hooks take effect in the next session. Before you push, run the same checks CI runs:

```bash
python3 scripts/validate.py          # manifests, frontmatter, Python syntax, version sync
claude plugin validate .             # Claude Code's own manifest check
```

Retrospective recommendations that target an agent or skill belong here, as an issue or a PR. Ones
that target a standard, the profile or the domain docs belong in the project.

### Releasing

1. Bump `version` in `.claude-plugin/plugin.json` **and** `.claude-plugin/marketplace.json` (the
   validate script checks they match). Use semver: a profile change that projects must make is a
   minor version before 1.0, a major one after.
2. Add a CHANGELOG entry.
3. Commit, tag `vX.Y.Z`, and push with tags. Installed copies pick up the new version on their next
   update.

## License

MIT. See [LICENSE](LICENSE).
