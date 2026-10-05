# Getting started

Set a project up in this order. Each step gives the next one something to work from: the PRD gives
the domain docs their words, the domain and standards give OpenSpec its context, the backlog says
which use case comes first, and all of it gives the first use case a solid base.

```
1. PRD (grill-me) ─▶ 2. init ─▶ 3. write-domain ─▶ 4. write-standards ─▶ 5. openspec config + README
   ─▶ 6. plan-use-cases (BACKLOG.md) ─▶ 7. write and build use cases, one at a time
```

You don't need perfect docs before your first use case. A short PRD, a glossary, a few business
rules and one or two standards are enough. They grow as the pipeline runs.

## 1. Write a PRD with grill-me

Start with a product requirements document (PRD): what you are building, for whom, and why. Write it
before anything else, even on an existing codebase. It records decisions that the code can't show,
such as the goals, the users, what is out of scope and what success looks like.

Use the `grill-me` skill from Matt Pocock's
[skills plugin](https://github.com/mattpocock/skills) to build it. It interviews you one round at a
time, recommends an answer to each question, and keeps going until every decision is settled. A
grilling finds the gaps that a PRD written in one pass misses. To install the plugin:

```
/plugin install mattpocock-skills@claude-plugins-official
```

Then run it and ask for a PRD at the end:

```
/mattpocock-skills:grill-me I want to build <your product idea>. Grill me until we agree
on the product, then write it up as a PRD in docs/prd.md.
```

A useful PRD covers:

- **Problem and goals:** what is wrong today, and how you will know it's fixed.
- **Users:** who they are and what each one needs.
- **Scope:** the main capabilities, and what is explicitly out of scope.
- **Constraints:** rules, deadlines, regulations and integrations you can't change.
- **Open questions:** what is still undecided.

Keep it at the business level. How the system is built belongs in the standards and the plans.

## 2. Set up the project

Install the OpenSpec CLI, run `openspec init`, then run `/sdlc-pipeline:init`. It writes the profile
(`.claude/sdlc-profile.md`) and creates the use-case, retrospective and session-report folders. See
the [README](../README.md#prerequisites) for the prerequisites.

## 3. Document the domain

Run `/sdlc-pipeline:write-domain`. It drafts the five domain files from the PRD, the code and the
other docs, then interviews you to confirm its drafts and fill the gaps. With a PRD in `docs/`, much
of the overview, the actors and the glossary are drafted for you rather than asked.

## 4. Choose the standards

Run `/sdlc-pipeline:write-standards`. Pick an architecture and the concerns you care about, then
keep, adapt or drop each rule. It writes `standards/` and updates the profile to cite the rules you
kept.

[domain-and-standards.md](domain-and-standards.md) covers both folders in full: what goes in them,
how the agents use them, and how the two skills build them.

## 5. Update the OpenSpec config and the README

Once `domain/` and `standards/` exist, bring the two files that describe the project up to date.
Neither skill edits them.

### `openspec/config.yaml`

OpenSpec adds the `context` to every planning artifact it writes, and adds each `rules` entry to
the artifact it names. The architect plans through OpenSpec, so this is where a plan learns what
the product is and where the project's knowledge lives. `openspec init` leaves it mostly empty.

- **`context`:** a short summary of the product from the PRD (what it is, for whom, the hard
  constraints) and pointers to the docs: the PRD, `domain/` (glossary terms, `BR-` rule ids) and
  `standards/`. Point to them rather than copy them. The context is added to every artifact, so
  keep it short.
- **`rules`:** what each planning artifact must contain in this project. For example, the
  specs use glossary terms and cite `BR-` ids, and the design cites the standard behind each
  decision. Rules about stack facts and gate checklists belong in the profile instead. See
  [profile.md](profile.md#profile-claudemd-or-openspecconfigyaml).

```yaml
schema: spec-driven

context: |
  Product: <one paragraph from the PRD: what it is, for whom, why>. Full PRD: docs/prd.md.
  Domain language: domain/glossary.md. Use its terms and no synonyms.
  Business rules: domain/business-rules.md. Cite rules by id (BR-<AREA>-<n>).
  Bounded contexts: domain/bounded-contexts.md. A change stays inside one unless the proposal
  says why.
  Standards: standards/*.md, numbered §n and cited from .claude/sdlc-profile.md.

rules:
  proposal:
    - Name the bounded context the change belongs to.
  design:
    - Cite the standard (standards/<file>.md §n) behind each architectural decision.
  specs:
    - Use glossary terms. Cite the business rule id each requirement enforces.
  tasks:
    - Add a task to record any new term or durable business rule in domain/.
```

Ask Claude to draft it, then review every line:

```
Update openspec/config.yaml. Summarise the product from docs/prd.md in the context, and
point to domain/ and standards/ rather than copying them. Add rules per artifact for
using glossary terms, citing BR- ids and citing standards. Don't repeat anything already
in .claude/sdlc-profile.md.
```

### `README.md`

The README is the first thing people and agents read. `init` reads it for the build and test
commands, and `write-domain` reads it for the business, so a stale README produces a wrong profile
and wrong domain docs. Check that it:

- describes the product the way the PRD does, and links to the PRD;
- gives the same build and test commands as the profile's **Verify** command;
- points to `domain/`, `standards/`, `use-cases/` and `BACKLOG.md` (once step 6 writes it), and says how a change is made (a use case run
  through `/sdlc-pipeline:build-use-case`).

```
Check README.md against docs/prd.md, domain/, standards/ and .claude/sdlc-profile.md.
Fix anything out of date and add links to those docs. Show me the diff first.
```

Repeat step 5 whenever the PRD, the domain or the standards change a lot.

## 6. Plan the use cases

Run `/sdlc-pipeline:plan-use-cases`. It reads the PRD and the domain docs, proposes the use cases the
product needs, interviews you to agree the order, and writes `BACKLOG.md` at the project root. The
aim is a **working product as soon as possible**, then one improvement at a time:

- **MVP:** the fewest use cases that let the primary actor reach the product's core goal end to end,
  main flows only. Every candidate gets the same question: *"Can the primary actor reach the core goal
  without this?"* If yes, it waits. The skill asks it again whenever you try to add to the MVP.
- **Increments:** one use case each, or one extension of an earlier one, most valuable first. Each
  leaves a product someone would rather use than the one before.
- **Later:** ideas worth keeping that aren't ordered yet.

Each entry is a checklist item with an id (`B-3`), the actor, the goal and why it sits where it does.
The backlog keeps itself up to date:

| When | What happens to the entry |
|------|---------------------------|
| `/sdlc-pipeline:write-use-case next` saves the use case | its first line links to the use case: `— written: UC-004` |
| `/sdlc-pipeline:build-use-case` archives the change | its box is ticked, it says `— built: UC-004, change <name>`, and the section count goes up (`MVP (3/4 built)`) |
| a use case is written or a change archived some other way | the next `plan-use-cases` run finds it and proposes the tick |

Re-run `plan-use-cases` when the PRD changes, or to re-order what's next. It keeps every id and
status, and shows you a diff before writing.

## 7. Write and build use cases

```
/sdlc-pipeline:write-use-case next                    # draft the next backlog entry as use-cases/UC-<n>-<slug>.md
/sdlc-pipeline:build-use-case use-cases/UC-003-….md   # run the pipeline; answer the two gates
```

Build the MVP entries first, in order. Once they are all ticked you have a working product; from
there, each increment makes it more valuable. `write-use-case <rough idea>` still works for an idea
that isn't in the backlog, and offers to add it.

[pipeline.md](pipeline.md) describes what happens from here.
