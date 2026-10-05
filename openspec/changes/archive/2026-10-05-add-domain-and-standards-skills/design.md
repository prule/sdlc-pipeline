## Context

`docs/domain-and-standards.md` defines the five domain files and what makes a good standard. The
agents depend on both: `write-use-case` and the architect read `domain/`, and the reviewers cite
`standards/<file>.md §<n>`. Agents find a standard only through a profile line that cites it.
Today `init` drafts those profile lines once from `standards/` and never touches an existing file.
For motivation, see proposal.md.

Constraints that shape the design:
- The plugin never names a language, build tool or framework.
- The plugin never writes project-owned files on update. A skill the user runs and confirms is not
  an update.
- Python is 3.8+ and standard library only.

## Goals / Non-Goals

**Goals:**
- A team with no `domain/` or `standards/` can create both in one sitting each.
- Every rule written to `standards/` is one the team chose to keep, not a default.
- Every kept rule is cited by the profile, so the agents read it.
- Both skills can be re-run to grow the docs without losing edits or renumbering rules.

**Non-Goals:**
- A complete catalogue. The first version ships five templates; adding one later is a new file.
- Keeping `standards/` in sync with the catalogue. Once rules are copied, the project owns them;
  catalogue updates don't flow back.
- A non-interactive agent version of either skill. These are interviews by nature.
- Decision records or ADRs. The domain docs state rules as they stand (see the docs page).

## Decisions

### D1. Two skills, not one

`write-domain` and `write-standards` are separate skills. The domain is about the business and the
standards are about engineering. Different people often answer them, and they are run at different
times. Names follow `write-use-case`.

*Alternative:* one `write-knowledge` skill with two modes. Rejected: one long interview, and a
vaguer trigger description.

### D2. Domain: mine first, then interview, in dependency order

`write-domain` reads the code, README, `CLAUDE.md`, docs and existing use cases, and drafts every
file it can. Anything inferred rather than found is marked `(to confirm)`. It then interviews the
user with `AskUserQuestion`, in this order:

```
overview --> actors & personas --> glossary --> bounded contexts --> business rules
```

Each step supplies the words for the next. Rules come last because they are written in glossary
terms and belong to a context. On a greenfield project nothing is mined and the whole flow is
interview. Content stays at the business level, using the "What to leave out" rules from the docs
page.

On a re-run, the skill reads the existing files, proposes additions and changes, and keeps every
existing business rule id. New rules take the next free id in their prefix. It never deletes an
entry without the user saying so.

*Alternative:* interview only. Rejected: most of a brownfield project's glossary is already in its
code and docs, and asking for it again wastes the user's time.

### D3. Standards catalogue holds rule libraries

Each template is a list of concrete, numbered rules, not a set of questions. People can react to a
concrete rule much more easily than they can write one from nothing. Each rule has this shape:

```markdown
## §1 The domain depends on nothing outside itself
Why: business rules stay testable and survive a change of framework or storage.
Check: no code in <domain module> refers to an adapter, framework or I/O library.
Profile: implementation-rule, code-review
```

- `Why` and `Check` are required; they become the rule's reason and what a reviewer looks for.
- `Profile` lists the profile sections that cite the rule: any of `implementation-rule`,
  `plan-review`, `verification`, `code-review`.
- `<angle brackets>` are stack blanks, such as `<domain module>`, `<migration tool>` or
  `<contract file>`. The interview fills them in. This is what keeps the catalogue stack-agnostic:
  the plugin describes the pattern, and the project supplies the names.
- Six to eight rules per template, to keep the interview short.

Layout: `templates/standards/architecture/{layered,hexagonal}.md` and
`templates/standards/concerns/{testing,api,persistence}.md`. Architecture templates are
alternatives (pick one); concern templates combine (pick any). A concern template may offer a
choice inside it, such as contract-first or code-first in `api`, written as two alternative rules
of which the user keeps at most one.

*Alternative:* question banks that the interview turns into rules. Rejected by the user: slower,
and the quality depends on the interview.

### D4. Keep, adapt or drop every rule

For each chosen template, `write-standards` presents its rules in batches (one template per
`AskUserQuestion` round, not one rule per question). For each rule the user picks:

- **keep:** copy as written, with blanks filled in;
- **adapt:** the user rewords it; the skill checks the result is still checkable and has a reason;
- **drop:** leave it out.

The question asked for each rule is "Would you reject a change that broke this?" This puts into
practice the docs page's rule that aspirations aren't standards. A rule the user would not enforce
is dropped.

On a brownfield project, the skill first looks for evidence that the code already follows a rule
and preselects **keep** for those, showing the evidence. Preselection is only a suggestion; the
user still answers every rule.

Kept rules are written to `standards/<concern>.md` (`architecture.md` for the architecture
template), renumbered `§1…§n` in the project's file. On a re-run against an existing file, new
rules are appended with the next number. Existing numbers never change, because retrospectives and
findings cite them.

### D5. The skill edits the profile in place, with a diff

After writing `standards/`, the skill updates `.claude/sdlc-profile.md`:

- For each kept rule, it adds a line under each section named in the rule's `Profile` field,
  citing `standards/<file>.md §<n>`.
- It touches only lines that cite a file under `standards/`. Commands, paths, git settings, task
  order and formatting are left alone.
- It matches existing lines by the file and section they cite, not by exact text. A line the user
  has reworded is updated, not duplicated.
- It shows the full diff and writes only after the user confirms. If the profile doesn't exist, it
  tells the user to run `init` first.

This is a deliberate exception to `init`'s "never touch an existing file" stance. The docs page
says a standard nobody cites is rarely read, and copying lines in by hand is the step people skip.
A user-invoked skill writing after a confirmed diff is not a plugin update, so the
project-ownership constraint holds.

*Alternatives:* print the lines for the user to paste (rejected: they won't), or edit only on the
first run (rejected: standards change after that too).

### D6. `init` points to the new skills

Current wording of `skills/init/SKILL.md` step 4:

> **Domain docs.** If the domain folder is missing, tell the user the agents rely on it (glossary,
> business rules, bounded contexts, actors and personas, overview) and offer to draft a skeleton.
> Don't create it unasked.

Replacement:

> **Domain and standards docs.** If the domain folder is missing, tell the user the agents rely on
> it (glossary, business rules, bounded contexts, actors and personas, overview) and suggest
> `/sdlc-pipeline:write-domain`. If the standards folder is missing, suggest
> `/sdlc-pipeline:write-standards`. Don't create either.

This fixes a gap, not a recorded failure: the skeleton `init` offered was empty headings, and the
rest was up to the user. No retrospective or session report covers it yet.

### D7. Validation

`scripts/validate.py` gains two checks over `templates/standards/**/*.md`:

1. Every `## §<n>` rule has `Why:`, `Check:` and `Profile:` lines, and `Profile` values come from
   the four allowed names.
2. No template contains a name from a short denylist of common languages, build tools and
   frameworks (case-insensitive, whole word).

The denylist is a tripwire, not a guarantee. It catches the obvious slips; review catches the rest.

### Staying stack-agnostic and leaving OpenSpec alone

The catalogue and both skills describe patterns and practices. Stack names live only in the
project's filled-in `standards/` and profile, and come from the user or the project's own code.
Neither skill reads or writes OpenSpec artifacts or `openspec/config.yaml`. Rules about planning
artifact content stay the project's own business (see `docs/profile.md`, "Profile, CLAUDE.md or
openspec/config.yaml?").

## Risks / Trade-offs

- [Teams keep every rule to get through the interview] → The "would you reject a change?" question
  for each rule; the docs say fewer rules is better; the session report's context-ingestion panel
  shows rules that are never cited.
- [Brownfield evidence is wrong] → Evidence only preselects and is shown to the user; it never
  decides.
- [Profile matching duplicates or misses a hand-edited line] → Match by cited file and section; the
  diff is always shown before writing, so the user sees any duplicate.
- [Interview fatigue: five templates is up to about 40 rules] → One batch per template, six to
  eight rules each; the user can stop after any template and re-run later.
- [Catalogue rules drift from good practice over time] → Templates are versioned with the plugin.
  Projects own their copies, so a catalogue fix reaches a project only if they re-run the skill.
- [Denylist false positives, such as a common word that is also a tool name] → Keep the list short
  and limited to unambiguous names.

## Migration Plan

None. Both skills are new and opt-in. Existing projects keep their docs and profile untouched
until they run a skill. Rollback is reverting the release; any files a skill wrote stay with the
project.
