---
name: write-standards
description: Build the project's standards/ docs from the plugin's catalogue of architecture and concern templates. The user keeps, adapts or drops every rule, the kept rules are written to standards/ with the stack details filled in, and the profile is updated to cite them. Use when the user wants to create, choose, write or extend coding or engineering standards, or when init reports the standards folder is missing.
argument-hint: "[templates to start from, e.g. \"hexagonal, testing\"]"
---

Build the project's **standards**: the rules a plan and its code must follow, which the reviewers
cite in their findings. A standard is a rule the team enforces today, not good advice. Starting
point from the user, if any:

$ARGUMENTS

What makes a good standard is set by `${CLAUDE_PLUGIN_ROOT}/docs/domain-and-standards.md` ("The
standards docs"). Read it first and follow it.

## The catalogue

Templates live under `${CLAUDE_PLUGIN_ROOT}/templates/standards/`:

- `architecture/*.md`: alternative styles. The project picks **at most one**.
- `concerns/*.md`: testing, api, persistence and so on. The project picks **any number**.

Each rule is a `## §<n>` heading with `Why:` (the reason), `Check:` (what a reviewer looks for),
`Profile:` (the profile sections that cite it) and, for alternatives, `Alternative to: §<m>`.
`<Angle brackets>` are stack blanks. The catalogue is read-only; never edit it.

## Steps

1. **Load context.** Read `.claude/sdlc-profile.md`. If it is missing, tell the user to run
   `/sdlc-pipeline:init` first and stop; don't create a profile. Note the standards path (default
   `standards/`) and read any standards files that already exist.

2. **Choose templates.** List the catalogue. Use `AskUserQuestion`: one single-choice question for
   the architecture template (with "none" as an option) and one multiple-choice question for the
   concern templates. Skip a template the project already has a standards file for unless the user
   wants to extend it.

3. **Look for evidence.** If the project has code, check each chosen rule against it. Note where the
   code already follows a rule (with a file or two as evidence) and where it clearly doesn't. Also
   collect what the stack blanks should be: the project's real paths, tools and engines.

4. **Keep, adapt or drop every rule.** Work one template per round. For each rule, show its text,
   its `Why`, and any evidence, and ask: **"Would you reject a change that broke this?"** The
   answers are:
   - **keep**: use it as written, with the blanks filled in;
   - **adapt**: the user rewords it;
   - **drop**: leave it out.

   Preselect **keep** for a rule the code already follows, and say so; it is still the user's
   answer. Fill each blank from the evidence and confirm it, or ask. For alternatives, keep at most
   one. An adapted rule must still say what a reviewer can check and why it matters. If it doesn't,
   ask for a checkable version before writing it. The user may stop after any template; write what
   has been decided so far.

5. **Write `standards/`.** One file per template: `standards/architecture.md` for the architecture
   template, `standards/<template>.md` for each concern. Start the file with a one-line title. Write
   each kept rule as `## §<n> <rule>` followed by its `Why:` line and `Check:` line. Drop the
   `Profile:` and `Alternative to:` lines; they only steer this skill. Number rules `§1` to `§n` in
   the order kept. No `<blank>` may be left. If the file already exists, append new rules with the
   next free number and never renumber or rewrite existing ones. Show the user each file before you
   write it.

6. **Update the profile.** Draft one line per kept rule in each profile section its `Profile:`
   names:

   | `Profile:` value | Profile section |
   |------------------|-----------------|
   | `implementation-rule` | **Implementation rules** |
   | `plan-review` | **Review checklist → Plan review (spec-reviewer)** |
   | `verification` | **Review checklist → Verification (qa)** |
   | `code-review` | **Review checklist → Code review (senior-dev)** |

   Each line states the rule in a few words and cites it as `standards/<file>.md §<n>`. Then:
   - Change only lines that cite a file under `standards/`. Leave every other line and section
     (Commands, Paths, Git, Task order, Formatting) exactly as it is.
   - Match an existing line by the file, rule number and profile section it cites, not by its
     wording. Update a matched line; never add a second line for the same rule in the same section.
   - Remove the placeholder lines from the template (lines in `<angle brackets>`) in the sections
     you fill.
   - If an existing line cites a `standards/` file without a rule number, show it in the diff and
     ask whether the new lines replace it.
   - Show the full diff of the profile. Write only after the user confirms. If they decline, leave
     the profile unchanged and print the lines instead.

7. **Report** the files written, the rules kept, adapted and dropped per template, and whether the
   profile was updated. Suggest re-running this skill to add a template later, and
   `/sdlc-pipeline:write-domain` if the project has no domain docs. Once both exist, suggest
   updating `openspec/config.yaml` and the README to point at them (see
   `${CLAUDE_PLUGIN_ROOT}/docs/getting-started.md`, step 5), then
   `/sdlc-pipeline:write-use-case <idea>`.

## Rules

- **The team decides.** Never write a rule the user didn't keep or adapt. The catalogue is a source
  of candidates, not a default.
- **Fewer is better.** Every agent reads these docs on every run. If the user is unsure about a
  rule, suggest dropping it; it can be added later when a retrospective shows it's needed.
- **No tool rules.** Formatting and lint rules belong in the formatter and linter config, not in
  `standards/`.
