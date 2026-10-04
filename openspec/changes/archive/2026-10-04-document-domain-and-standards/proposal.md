## Why

The README tells users to add a `domain/` and a `standards/` folder, and says the agents ground their
work in them, but stops there. It doesn't say what goes in each folder, how the agents use them, or
how to write them. New users either skip them, which leaves the plans only as good as the use case,
or guess at the contents. These folders are the main lever a project has on plan and review quality,
so the docs should explain them.

## What Changes

- **README.md:** a new "Domain and standards" section between Prerequisites and Install. It says in
  a few lines what each folder is for, which agents read it, and the fastest way to start one, then
  links to the new guide. The Prerequisites bullet is shortened to point at that section.
- **docs/domain-and-standards.md (new):** the full guide.
  - *Domain docs:* the five files the agents expect (overview, glossary, business rules, bounded
    contexts, actors and personas), what each should cover, a short example of each, and what to
    leave out (implementation detail, anything that belongs in a use case).
  - *Standards docs:* what a standard should cover (rules that are checkable, numbered so findings
    can cite `standards/<file>.md §<n>`), suggested files, how standards relate to the profile (the
    profile indexes, the standards hold the detail), and what to leave out (anything a linter or
    formatter already enforces).
  - *Creating them:* by hand, by asking Claude to draft them from the codebase and existing docs,
    with `init` (which offers a domain skeleton and drafts the profile from `standards/`), and
    growing them over time from `write-use-case` domain gaps, architect tasks that record new terms,
    and retrospective recommendations.
  - *Keeping them useful:* short beats complete; check the Context ingestion panel in the session
    report to find docs that are never read or never cited.
- **docs/pipeline.md and docs/profile.md:** link to the new guide where they mention `domain/` and
  `standards/`.
- **CHANGELOG.md:** a 0.2.1 entry.

No agent, skill, hook, script or template changes. Host projects need do nothing.

**Semver:** patch, 0.2.0 → 0.2.1. Documentation only; no behaviour or profile change.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None. This change is documentation only, so it sets `skip_specs: true`.

## Impact

- Files: `README.md`, `docs/domain-and-standards.md` (new), `docs/pipeline.md`, `docs/profile.md`,
  `CHANGELOG.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`.
- The guide must stay stack-agnostic: examples use a neutral business domain and name no language,
  framework or build tool.
