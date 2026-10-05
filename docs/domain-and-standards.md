# Domain and standards docs

The agents know their roles, and the profile tells them your stack. Two folders in your project tell
them the rest:

- **`domain/`**: what the business is. Its words, its people, its rules and where its boundaries
  are.
- **`standards/`**: how your team builds software. The rules a plan and its code must follow.

Neither is required. Without them the pipeline still runs, but the use case is the only source of
business knowledge, and the reviewers can only judge the plan and the code against general good
practice. With them, the plan uses your terms, honours your rules, and every review finding can cite
the rule it breaks.

The paths are set in the profile (**Paths → Domain knowledge** and **Standards**). The defaults are
`domain/` and `standards/`. Both folders belong to your project; a plugin update never touches them.

## How the agents use them

| Who | `domain/` | `standards/` |
|-----|-----------|--------------|
| `write-use-case`, `use-case-writer` | Reads all of it for the actor, bounded context, terms and rules. Flags **domain gaps**: terms, actors or rules the use case needed but couldn't find. | Not read. Use cases stay at the business level. |
| `architect` | Reads at least the glossary and business rules. Adds a task to record any new term or durable rule. | Applies them while writing the plan, through the profile's rules. |
| `spec-reviewer` | Checks the plan uses glossary terms, honours the business rules, stays inside its bounded context, and records new knowledge. | Checks the plan against the profile's **Plan review** checklist and the standards it cites. |
| `junior-dev` | — | Follows the profile's **Implementation rules** and the standards they cite. |
| `qa`, `senior-dev` | — | Check the code against their checklist sections. Each finding cites `standards/<file>.md §<n>`. |
| `write-domain` | Drafts and grows it, interviewing you for what it can't find. | — |
| `write-standards` | — | Writes it from the catalogue rules you keep, and updates the profile lines that cite it. |
| `init` | Suggests `write-domain` if the folder is missing. | Drafts the profile's rules, task order and checklists from it; suggests `write-standards` if it is missing. |
| Retrospective | Recommends domain doc changes when a gap caused a defect. | Recommends a new or clearer standard when one was missing or unclear. |

The profile is the link between the agents and `standards/`. Agents find a standard through the
profile line that cites it, so a standard nobody cites in the profile is rarely read.

## The domain docs

Use these five files. The agents and the use-case template refer to them by name.

| File | What it covers |
|------|----------------|
| `overview.md` | What the business does, for whom, and why. One page. The context a new team member needs before reading anything else. |
| `glossary.md` | Every business term, with one meaning each. Include synonyms to avoid ("we say *member*, not *user* or *customer*"). |
| `business-rules.md` | The durable policies: limits, eligibility, ordering, visibility, what happens when. Each rule has a stable id so use cases and plans can cite it. |
| `bounded-contexts.md` | The parts of the business that use words differently or change for different reasons, what each one owns, and how they talk to each other. |
| `actors-and-personas.md` | Who uses the system and what they want from it. Include other systems that act on it. |

### Examples

These illustrate the level of detail, for a small lending library. Write your own.

```markdown
<!-- glossary.md -->
- **Member:** a person registered with the library who may borrow items. Not "user" or "patron".
- **Loan:** one item lent to one member, from checkout until it is returned.
- **Hold:** a member's place in the queue for an item that is out on loan.
```

```markdown
<!-- business-rules.md -->
- **BR-LOAN-1:** A member may have at most 5 loans at once.
- **BR-LOAN-2:** A loan lasts 21 days. A member may renew it twice, unless another member has a
  hold on the item.
- **BR-HOLD-1:** Holds are filled in the order they were placed.
```

```markdown
<!-- bounded-contexts.md -->
## Circulation
Owns loans, holds and returns. Knows a member only by id and loan limit.

## Catalogue
Owns items and their descriptions. Doesn't know who has borrowed what.
```

```markdown
<!-- actors-and-personas.md -->
- **Member:** borrows and returns items, places holds. Wants to know when an item will be free.
- **Librarian:** checks items in and out, overrides limits with a reason.
- **Payment provider (system):** confirms fine payments.
```

### What to leave out

- **Implementation.** No tables, endpoints, classes, screens or technologies. The domain docs
  describe the business, which outlives any system built for it.
- **Single features.** One use case's behaviour belongs in that use case. A rule goes in
  `business-rules.md` once more than one use case depends on it, or it would hold even if the
  feature were rebuilt.
- **History and debate.** State the rule as it stands. Decisions and their reasons belong in your
  decision records, if you keep them.

## The standards docs

A standard is a rule your team has agreed on that a reviewer can check. Good standards are:

- **Checkable.** "Every requirement has a test that exercises its failure path" can be checked.
  "Write good tests" can't.
- **Numbered.** Number the sections or rules (`§1`, `§2`, …). Findings cite `standards/testing.md §3`,
  and a retrospective can then show which rule keeps being broken.
- **Explained in one line.** Give the reason. A reviewer applies a rule better when it knows what
  the rule protects.
- **Short.** Every agent that reads a standard pays for it in context on every run.

Split them by concern, one file each. For example:

| File | Typical rules |
|------|---------------|
| `architecture.md` | Layers or modules and what each may depend on; where business logic lives. |
| `testing.md` | What must be tested and at which level; what a test may mock; test naming. |
| `api.md` | Contract-first or not; error format; versioning; naming. |
| `persistence.md` | How schema changes are made; what must never change once released. |
| `e2e-testing.md` | Which flows get end-to-end tests; how tests find elements; how tests are structured (for example, the Screenplay pattern). |
| `security.md` | Input validation, secrets, authorisation checks. |
| `observability.md` | What must be logged or measured, and what must never be logged. |

### Standards and the profile

The profile is an index; the standards hold the detail. For each standard, the profile has:

- a one-line **Implementation rule**, citing the file, for anything the junior dev must do;
- a line in each **Review checklist** section saying what that gate checks, citing the file.

After you add or change a standard, update the profile lines that cite it. See
[profile.md](profile.md).

### What to leave out

- **What a tool already enforces.** Formatting and lint rules belong in the formatter and linter
  config. The profile's **Formatting** section tells the agents who formats.
- **Tutorials.** A standard says what to do, not how the language or framework works.
- **Aspirations.** If the team doesn't follow a rule today and won't reject a change for breaking it,
  it isn't a standard yet.

## Creating them

You don't need complete docs to start. A glossary, a handful of business rules and one or two
standards are enough to see the difference in the first plan. Two skills build them with you.

Write a PRD first, with the `grill-me` skill, and save it in `docs/`. `write-domain` drafts from
it, so the interview only asks about what the PRD leaves out. When both folders exist, update
`openspec/config.yaml` and the README to point at them. [getting-started.md](getting-started.md)
covers the whole order, with an example config.

### `write-domain`

`/sdlc-pipeline:write-domain` drafts the five domain files from what the project already holds:
the PRD, code, README, `CLAUDE.md`, docs and use cases. It marks anything it inferred rather than found as
`(to confirm)`. Then it interviews you in this order, because each step gives the words for the
next:

```
overview --> actors and personas --> glossary --> bounded contexts --> business rules
```

It asks only about what it couldn't find, and gives each business rule an id (`BR-LOAN-1`). Run it
again to grow the docs: it shows additions as a diff, keeps existing ids, and never deletes an
entry you didn't ask it to. On a new project with no code, the whole thing is an interview.

### `write-standards`

`/sdlc-pipeline:write-standards` starts from a catalogue of ready-made rules in the plugin:

| Kind | Templates | Pick |
|------|-----------|------|
| Architecture | `layered`, `hexagonal` | at most one |
| Concerns | `testing`, `api`, `persistence`, `e2e-testing` | any |

The catalogue names no language, tool or framework. Where a rule needs one, it has a blank such as
`<migration tool>`, which the skill fills in from your code or your answers.

For every rule in the templates you pick, the skill asks: *would you reject a change that broke
this?* You **keep** it, **adapt** it or **drop** it. If the code already follows a rule, the skill
says so and shows where, but the answer is still yours. Only kept and adapted rules are written to
`standards/`, numbered `§1` to `§n`. Keep only what you enforce today; you can add rules later.

Then it updates `.claude/sdlc-profile.md` so the agents read the new rules: one line per kept rule in
each section that needs it (Implementation rules and the three Review checklist sections), citing
`standards/<file>.md §<n>`. It changes only lines that cite `standards/`, shows you the full diff,
and writes only if you confirm. This is the one skill that edits an existing profile, because a
standard the profile doesn't cite is rarely read.

Run it again to add a template or extend a file. New rules get the next number; existing numbers
never change, because findings and retrospectives cite them.

### Without the skills

You can also ask Claude to draft the docs directly, then review every line. A draft is a starting
point; a wrong rule here becomes a wrong plan later. For example:

```
Draft domain/ for this project: overview.md, glossary.md, business-rules.md,
bounded-contexts.md and actors-and-personas.md. Work from the code, README and docs.
Business language only, no implementation detail. Give each business rule an id.
Mark anything you inferred rather than found as "(to confirm)".
```

```
Draft standards/ from the conventions this codebase already follows: architecture.md
and testing.md to start. Only include rules the code consistently follows and a
reviewer could check. Number each rule and give its reason in one line.
```

Then edit `.claude/sdlc-profile.md` so it cites the new standards.

### With `init`

`/sdlc-pipeline:init` drafts the profile's Implementation rules, Task order and Review checklists from
whatever is in `standards/` when it creates the profile. If `domain/` or `standards/` is missing, it
suggests `write-domain` or `write-standards`. It never overwrites a file that already exists.

### Grow them as you go

The pipeline tells you what's missing:

- **`write-use-case` domain gaps.** When a use case needs a term, actor or rule the domain docs
  don't have, the skill says so and offers to add it.
- **Architect tasks.** When a change introduces a new term or durable rule, the plan includes a task
  to record it in `domain/`, and the spec-reviewer checks it's there.
- **Retrospectives.** Each finding has a root cause. "Missing or unclear standard" and domain gaps
  come with a recommended change to a standard or domain doc. A finding that recurs across runs is
  ranked first.

## Keeping them useful

Shorter is usually better. The session report's **Context ingestion** panel shows, for each doc in
`domain/` and `standards/`, how often it was read, whether it was read before the agent wrote
anything, how often it was cited, and its size. Look for:

- **Never read:** nothing points to it. Cite it from the profile, or delete it.
- **Read but never cited:** it may not be saying anything the agents can use.
- **Large and rarely used:** flagged `wordy / low-signal?`. Trim it.

To find out whether a doc helps rather than just whether it is read, run the same use case with and
without it. See [evaluating-the-pipeline.md](evaluating-the-pipeline.md).
