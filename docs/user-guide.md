# User Guide

How to use AI Coding Golden Paths day to day: bootstrap a project, choose what goes in it, and switch or add coding agents.

Related: [Glossary](glossary.md) · [Architecture](architecture.md) · [Personal context](personal-context.md)

## What it is

A generator that gives a project vendor-neutral engineering standards plus the native configuration for your AI coding agent(s). The standards are written once in `docs/engineering/` inside your project. CLAUDE.md, `.claude/`, and AGENTS.md just point to them. After bootstrap, the project is independent: nothing depends on this repository.

## Setup

```bash
git clone <this repository> ai-coding-golden-paths
cd ai-coding-golden-paths
python -m pip install -e '.[dev]'     # Python 3.10+; installs PyYAML (+ pytest)
```

All commands below run from this repository's root. `--target` can be any directory: new, empty, or an existing project.

## Create a new project

```bash
python bootstrap/init.py --target ../my-app --tool claude --tool codex --preset fastapi-rag --dry-run
python bootstrap/init.py --target ../my-app --tool claude --tool codex --preset fastapi-rag
```

Then:
1. Fill in `../my-app/docs/engineering/PROJECT.md` (overview, architecture, commands). Every agent reads it.
2. Review the generated files and commit them, including `.golden-paths.yaml`.

The project name in the generated headings defaults to the target directory name. Use `--project-name "Billing API"` to override it.

## Choose profiles

Pick one profile per technology or domain the project actually uses:

| You are building | Profiles |
|------------------|----------|
| Any Python service | `runtime/python-backend` |
| A FastAPI service | `runtime/fastapi` (adds `python-backend` automatically) |
| A Next.js App Router frontend | `runtime/nextjs` |
| Retrieval over documents (search, Q&A, citations) | `ai/rag` |
| A model that calls tools in a loop | `ai/agentic-ai` |

```bash
python bootstrap/init.py --target ../my-app --tool claude --profile runtime/fastapi --profile ai/rag
```

Only select what applies. Each profile adds guidance the agent will follow. To see what a profile says, read `profiles/<category>/<name>/guidance.md`.

## Choose a preset

A preset is a shortcut for a common profile list:

| Preset | Equals |
|--------|--------|
| `fastapi-rag` | python-backend + fastapi + rag |
| `fullstack-agentic-ai` | python-backend + nextjs + agentic-ai |

You can combine a preset with extra profiles. Duplicates are ignored:

```bash
python bootstrap/init.py --target ../my-app --tool codex --preset fastapi-rag --profile ai/agentic-ai
```

## Choose Claude Code vs Codex

`--tool` decides which instruction files are generated. The engineering content is identical either way.

| `--tool` | You get |
|----------|---------|
| `claude` | `CLAUDE.md`, `.claude/rules/` (path-scoped profile rules), `.claude/skills/` (one per workflow), `.claude/agents/code-reviewer.md` |
| `codex` | `AGENTS.md` |
| both | all of the above, sharing one `docs/engineering/` |

If anyone on the team uses the other tool, or might switch, generate both. It costs a few small files. Details: [Architecture: Adapters](architecture.md#adapters).

## Switch tools (fallback)

Already set up for one tool? Add the other at any time. You don't repeat the preset or profiles, because the selection is read from `.golden-paths.yaml`:

```bash
python bootstrap/init.py --target ../my-app --tool codex
```

Only the new entry files are created (here `AGENTS.md`), and `docs/engineering/` is untouched. Your architecture, standards, profiles, and workflows carry over unchanged. Why this works: [ADR-0006](decisions/adr-0006-single-neutral-knowledge-tree.md).

"Add another adapter to an existing project" means exactly this: re-run with the new `--tool`. Writing a *new* adapter for an unsupported agent is a different task; see [Adding an adapter](adding-an-adapter.md).

## Use dry-run

Add `--dry-run` to any command to see the plan without writing anything:

```text
note: reusing recorded selection from .golden-paths.yaml
  create     AGENTS.md
  keep       docs/engineering/PROJECT.md  (project-owned seed; never regenerated)
  unchanged  CLAUDE.md
  ...
1 create, 1 keep, 19 unchanged
dry run: nothing was written.
```

| Word | Meaning |
|------|---------|
| `create` | New file will be written |
| `update` | A generated file you never edited will be refreshed |
| `unchanged` | Already identical |
| `keep` | Left alone: you edited it, or it is the `PROJECT.md` seed |
| `conflict` | A file exists that the generator did not write. The run aborts and nothing is written (exit code 2) |

The full rules are in [Architecture: Safe writing](architecture.md#safe-writing).

## Personal context

Keep personal paths, sandbox URLs, and preferences out of generated files. Put them in `~/.claude/CLAUDE.md`, a git-ignored `CLAUDE.local.md`, or `~/.codex/AGENTS.md`. See [Personal context](personal-context.md).

## Normal lifecycle

1. **Bootstrap** with `--dry-run`, then for real.
2. **Fill in** `docs/engineering/PROJECT.md` and commit everything.
3. **Work.** Agents follow CLAUDE.md or AGENTS.md, which lead into `docs/engineering/`.
4. **Evolve standards in the project.** Edit `docs/engineering/*` or the entry files directly. They are yours, and re-runs keep your edits.
5. **Add a tool** when needed: re-run with `--tool <other>`.
6. **Pick up generator improvements** by re-running from a newer version of this repository. Unedited generated files are updated; edited ones are kept, so merge them by hand if you want the change.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Conflict on an existing `CLAUDE.md` or `AGENTS.md` | Rename it (for example `CLAUDE.md.old`), re-run, then merge your old content into the generated file or into `PROJECT.md` |
| Changing profiles with `--preset`/`--profile` on an initialized project | Not supported in v0.1; the run is refused. Edit `docs/engineering/` by hand, or regenerate into a fresh directory and copy across |
| Putting personal paths or URLs in `PROJECT.md` or `CLAUDE.md` | Move them to personal files ([Personal context](personal-context.md)) |
| Leaving `PROJECT.md` as TODOs | Agents then guess commands and architecture; fill it in first |
| Selecting every profile "just in case" | Irrelevant guidance dilutes what matters; select only what the project uses |
| Deleting `.golden-paths.yaml` | Re-runs can no longer tell generated files from yours, so every edited file becomes a conflict. Restore it from git |
| Editing guidance in this repository to fix one project | Edit the project's `docs/engineering/` instead. Change this repository only for reusable improvements |
