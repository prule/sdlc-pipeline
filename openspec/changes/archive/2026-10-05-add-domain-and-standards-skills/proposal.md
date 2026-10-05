## Why

The agents work best with `domain/` and `standards/` in place, but today a team has to write them
from a blank page or from a sample prompt in the docs. Most teams skip them, so plans don't use the
business's terms and review findings can't cite a rule. Two guided skills would make the docs cheap
to create. A small catalogue of ready-made rules would also give a team concrete standards to react
to, instead of having to write them from scratch.

## What Changes

- New skill `write-domain`. It reads the project's code, README and docs, drafts the five domain
  files (overview, actors and personas, glossary, bounded contexts, business rules), and interviews
  the user to confirm what it inferred and fill the gaps. It can be re-run: later runs add to the
  files and keep existing rule ids.
- New skill `write-standards`. The user picks one architecture template and any number of concern
  templates from a catalogue in the plugin. The skill walks through every rule, and the user keeps,
  adapts or drops each one. Kept rules are written to the project's `standards/`, numbered and with
  stack blanks filled in. The skill then edits the profile lines that cite `standards/`, after the
  user has seen a diff and confirmed it.
- New standards catalogue, read-only in the plugin: `layered` and `hexagonal` (architecture), and
  `testing`, `api` and `persistence` (concerns). Each rule has a reason, a check and the profile
  sections it belongs in. Rules name no language, build tool or framework; stack-specific details
  are blanks the interview fills in.
- `init`: the domain step points the user to `write-domain` instead of offering a skeleton. It also
  mentions `write-standards` when `standards/` is missing.
- `scripts/validate.py`: checks every catalogue rule has its required fields, and that no template
  contains a name from a short list of common languages, build tools and frameworks.
- Docs: `docs/domain-and-standards.md` rewritten around the two skills; README skills list updated.

## Capabilities

### New Capabilities
- `domain-authoring`: how `write-domain` builds and grows the five domain docs in a host project.
- `standards-authoring`: how `write-standards` turns catalogue templates into the project's
  `standards/` and wires the kept rules into the profile.

### Modified Capabilities
None. `run-retrospective` and `session-report` are unchanged.

## Impact

- **Components:** skills (`write-domain`, `write-standards` new; `init` changed), templates (new
  `templates/standards/` catalogue), scripts (`validate.py`), docs (`README.md`,
  `docs/domain-and-standards.md`), manifests and `CHANGELOG.md`.
- **Host projects:** need do nothing. Both skills are opt-in. `write-standards` edits
  `.claude/sdlc-profile.md` only when the user runs it and confirms the diff. This is a
  user-invoked edit, not a plugin update, so the rule that updates never touch project-owned files
  still holds.
- **Semver:** minor bump to 0.3.0. It adds new user-facing skills and changes `init`'s behaviour.
  No existing profile needs editing.
