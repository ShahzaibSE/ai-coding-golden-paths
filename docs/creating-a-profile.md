# Creating a Profile

A practical guide for maintainers adding technology or domain guidance. For the formal rules each profile must satisfy, see the [Profile contract](profile-contract.md). That document is authoritative; this one is the procedure.

Related: [Glossary](glossary.md) · [ADR-0002: Profiles](decisions/adr-0002-profiles-instead-of-monolithic-templates.md)

## Core ≠ Profile ≠ Preset ≠ Adapter

Before writing anything, put the content in the right layer:

| Layer | Holds | Example | Not here |
|-------|-------|---------|----------|
| **Core** | Rules true for *every* project | "Every bug fix starts with a reproducing test." | Anything tied to a language, framework, or domain |
| **Profile** | Rules true only when a technology or domain is present | "Never block the event loop in async code." | Universal rules; vendor or tool names |
| **Preset** | A named list of profiles | `fastapi-rag: [python-backend, fastapi, rag]` | Any guidance at all ([ADR-0004](decisions/adr-0004-presets-are-composition-only.md)) |
| **Adapter** | How one coding agent finds the knowledge | Claude rule files, AGENTS.md layout | Engineering knowledge ([ADR-0003](decisions/adr-0003-adapter-pattern-for-coding-agents.md)) |

Test: *Would this sentence be true in a project without this technology?* If yes, it belongs in core, or it already exists there.

## When to create a profile

Create one when:
- a technology or domain brings rules that a reviewer would enforce, and those rules don't hold elsewhere;
- the guidance is reusable across projects, not specific to one codebase (that belongs in the project's `PROJECT.md`).

Split an existing profile when part of it holds only for one framework or library. `runtime/fastapi` is split from `runtime/python-backend` because layering, async, errors, and testing hold for any Python framework, while `Depends()` and `dependency_overrides` do not. The specific profile declares `requires` on the generic one.

Don't create a profile for a personal preference, a single project's conventions, or a coding agent.

## What a profile may contribute

- **Guidance** (`guidance.md`): the full rules, in neutral language.
- **Summary** bullets: the 2–6 rules that matter in every session. Adapters copy them into CLAUDE.md and AGENTS.md.
- **File scope** (`applies_to`): globs where the guidance matters. Adapters turn them into path-scoped rules or "applies to" notes.
- **Workflows**: new procedures, such as evaluation or migration. Each becomes a skill or a linked workflow document.
- **Relationships**: `requires` and `conflicts`.

All of these are tool-neutral inputs. How each one is rendered is the adapter's job.

## What a profile must not contain

- Content already in core, or in another profile (validation rejects duplicate paragraphs).
- Coding-agent or vendor names, or instruction-file names (validation rejects them).
- Absolute paths, hostnames, credentials, or personal preferences.
- Overrides or patches of core workflows or other profiles. Profiles add; they never replace.
- Project-specific facts (service names, commands). Those go in the generated project's `PROJECT.md`.

## Step by step

1. **Choose the id.** Pick a category (`runtime`, `ai`, or a new one only if neither fits) and a unique slug: `profiles/<category>/<name>/`.
2. **Write `guidance.md`.** Start with a `# Title`. Use short sections of checkable rules; aim for 40–120 lines. Read the related core standards first so you don't restate them.
3. **Write `profile.yaml`.** Here is `ai/rag` as an annotated example (field rules: [Profile contract](profile-contract.md#profileyaml)):

   ```yaml
   name: rag                     # = directory name
   version: 0.1.0
   category: ai                  # = parent directory
   description: Retrieval-augmented generation - ...
   summary:                      # every-session rules only
     - Answers are grounded only in retrieved evidence; ...
   workflows:                    # a procedure this domain needs and core lacks
     - id: retrieval-evaluation
       file: workflows/retrieval-evaluation.md
       description: Use when changing chunking, embeddings, ...
   ```

   `rag` has no `applies_to` because RAG code has no reliable file pattern. `python-backend` does (`**/*.py`).
4. **Add workflows** under `workflows/` if the profile needs a procedure, and declare them. Ids must be unique across core and all profiles.
5. **Declare relationships.** Use `requires` for profiles yours builds on, and `conflicts` only for genuinely incompatible guidance. Prefer neither.
6. **Validate and test** (below).
7. **Add it to a preset**, if a common stack uses it.

## Testing a new profile

```bash
python bootstrap/validate.py     # contract, vendor neutrality, machine paths, duplicate paragraphs
pytest -q                        # composes your profile alone and paired with every other profile
python bootstrap/init.py --target /tmp/try-profile --tool claude --tool codex \
  --profile <category>/<name> --dry-run
```

Then generate without `--dry-run` into a scratch directory and read the output. Check the following:
- `docs/engineering/profiles/<name>.md` is your guidance;
- CLAUDE.md and AGENTS.md show your summary;
- a `.claude/rules/<name>.md` exists if you set `applies_to`;
- each workflow appears as a skill and in AGENTS.md.

Update `tests/test_profiles.py::test_initial_profiles_present` with the new id.

## Adding it to a preset

Add the id to an existing preset, or create `presets/<name>.yaml` with only `name`, `description`, and `profiles` (schema: [Profile contract](profile-contract.md#presets)). List generic profiles before specific ones; required profiles are added automatically anyway. If you add a preset, add its expected resolution to `tests/test_presets.py`.

## Good examples in this repository

- `runtime/python-backend`: generic, framework-free, with a clear file scope.
- `runtime/fastapi`: a thin, specific profile that builds on a generic one via `requires` and doesn't repeat it.
- `ai/rag` and `ai/agentic-ai`: domain profiles with no file scope, each adding an evaluation workflow instead of patching the core code-review workflow.
