# AI Coding Golden Paths

Reusable engineering foundations for AI coding agents. You write the knowledge once, and it is rendered into the native configuration of each agent. Claude Code and Codex are supported today.

> **Maturity: v0.1, early.** The structure, contract, and safety guarantees are tested. The profile catalog is small on purpose. Expect the content to evolve.

## The problem

Teams that use AI coding agents end up writing the same engineering rules again and again: in `CLAUDE.md`, in `AGENTS.md`, and in each new project. The copies drift apart. Switching agents means redoing the work, and the standards end up tied to one vendor's file format.

## The idea: golden paths

A *golden path* is the paved, recommended way to build something, with the standards, conventions, and workflows already decided. This repository holds those decisions in a **vendor-neutral** form and generates agent-specific configuration from them:

```
Engineering core  +  Profiles  +  Preset  +  Tool adapter  =  AI-ready project
```

| Piece | What it is | Example |
|-------|-----------|---------|
| **Core** | Universal standards and workflows, always included | testing, security, git workflow, code review, privacy baseline |
| **Profiles** | Composable guidance for one technology or domain | `runtime/python-backend`, `ai/rag` |
| **Presets** | Named combinations of profiles, with no content of their own | `fastapi-rag` |
| **Adapters** | Translate the knowledge into one agent's native config | `claude` → `CLAUDE.md` + `.claude/`; `codex` → `AGENTS.md` |

None of the content in core or the profiles mentions a vendor. Only the adapters know about specific tools.

## What a generated project looks like

```
my-app/
├── docs/engineering/        # the knowledge: one copy, tool-neutral, owned by your project
│   ├── PROJECT.md           # your architecture, commands, decisions (fill in once)
│   ├── standards/  governance/  workflows/  profiles/
├── CLAUDE.md                # --tool claude: concise contract + @imports
├── .claude/rules/           #   path-scoped profile guidance
├── .claude/skills/          #   one skill per workflow
├── .claude/agents/          #   code-reviewer
├── AGENTS.md                # --tool codex: project map + operating contract
└── .golden-paths.yaml       # what was generated (for safe re-runs; nothing reads it at runtime)
```

The project is independent after bootstrap. Nothing depends on this repository at runtime. See [`examples/fastapi-rag/`](examples/fastapi-rag/) for real output.

## Claude ↔ Codex fallback

The engineering knowledge lives once in `docs/engineering/`. The agent files only point to it, so you can switch agents, or use both, without redefining architecture, standards, profiles, testing expectations, security requirements, or workflows. Only the instruction mechanism differs.

```bash
# Set up for Claude Code today...
python bootstrap/init.py --target ../my-app --tool claude --preset fastapi-rag
# ...add Codex later: the recorded selection is reused and only AGENTS.md is created.
python bootstrap/init.py --target ../my-app --tool codex
```

This is tested, not assumed. [`tests/test_fallback.py`](tests/test_fallback.py) checks three things:
- the shared docs are byte-identical for every tool choice;
- every document, rule summary, and workflow is reachable from each agent's files;
- adding a tool later gives exactly the same result as generating both at once.

## Initial profiles

| Profile | Covers |
|---------|--------|
| `runtime/python-backend` | Python conventions, typing, service layering, error handling, async, pytest conventions (framework-agnostic) |
| `runtime/fastapi` | FastAPI app factory, models, `Depends`, error handlers, sync vs async handlers, testing. Requires `python-backend` |
| `runtime/nextjs` | TypeScript, App Router architecture, server/client boundaries, components, testing |
| `ai/rag` | Ingestion, retrieval, context assembly, grounding, insufficient evidence, source attribution, plus a retrieval-evaluation workflow |
| `ai/agentic-ai` | Tool boundaries, orchestration, state, failure handling, human checkpoints, plus an agent-evaluation workflow |

Presets:
- `fastapi-rag` = python-backend + fastapi + rag
- `fullstack-agentic-ai` = python-backend + nextjs + agentic-ai

## Quickstart

Requires Python 3.10+ and PyYAML (`python -m pip install -e '.[dev]'`).

```bash
python bootstrap/init.py --target ../my-app --tool claude --tool codex --preset fastapi-rag --dry-run
python bootstrap/init.py --target ../my-app --tool claude --tool codex --preset fastapi-rag
# then fill in ../my-app/docs/engineering/PROJECT.md
```

The generator never overwrites files it didn't write, and it keeps your edits to generated files. Choosing profiles, switching tools, dry-run output, and common mistakes are covered in the [User guide](docs/user-guide.md).

## Repository layout

```
core/          vendor-neutral standards, workflows, governance (+ core.yaml)
profiles/      <category>/<name>/{profile.yaml, guidance.md, workflows/}
presets/       *.yaml - profile lists only
adapters/      claude/, codex/ - renderers + templates
bootstrap/     init.py (CLI), compose.py, neutral.py, validate.py
tests/         pytest suite
examples/      committed generated output, snapshot-tested
docs/          architecture, profile contract, adding an adapter, personal context
```

## Documentation

- [User guide](docs/user-guide.md): bootstrap projects, choose profiles, presets, and tools, switch tools
- [Architecture](docs/architecture.md): how the layers, adapters, fallback, and safe writing work
- [Profile contract](docs/profile-contract.md): the formal rules for profiles and presets
- [Creating a profile](docs/creating-a-profile.md): step-by-step guide for maintainers
- [Adding an adapter](docs/adding-an-adapter.md): supporting another AI coding tool
- [Personal context](docs/personal-context.md): shared vs developer-local configuration
- [Glossary](docs/glossary.md): terminology
- [Architecture decisions](docs/decisions/README.md): why it is built this way (ADRs)

Before contributing, run `python bootstrap/validate.py` and `pytest -q`.

## Roadmap (not in v0.1)

- Nested `AGENTS.md` and scoped rules mapped to subdirectories (for example `web/` → nextjs) in monorepos
- Changing the profile set of an initialized project; removing a tool
- More adapters (Copilot, Gemini CLI, Cursor) through the same adapter contract

## License

MIT. See [LICENSE](LICENSE).
