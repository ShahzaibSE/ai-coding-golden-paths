# ADR-0003: Adapter Pattern for Coding Agents

## Status

Accepted

## Context

Each coding agent discovers instructions differently. Claude Code uses CLAUDE.md, path-scoped rules, skills, and subagents. Codex uses AGENTS.md files. More tools will follow. The vendor-neutral knowledge ([ADR-0001](adr-0001-vendor-neutral-engineering-core.md)) must reach each of them in its native form, without the knowledge layer knowing about any of them.

## Decision

Each tool gets an **adapter** in `adapters/<tool>/` with one function, `render(Composition) -> list[OutputFile]`. Adapters produce only entry-point files that point into the shared knowledge tree ([ADR-0006](adr-0006-single-neutral-knowledge-tree.md)). They may not write under `docs/engineering/`. Adapters are discovered by directory name. The fallback test suite runs against every discovered adapter automatically. See [Adding an adapter](../adding-an-adapter.md).

## Consequences

- Tool-specific concepts stay inside one directory per tool.
- Adding a tool means adding a directory and its tests; core, profiles, and bootstrap don't change.
- Each adapter uses its tool's strengths, such as Claude Code's path-scoped rules, without forcing them on others.
- Capabilities only one tool has (for example hooks) create asymmetry between tools. v0.1 avoids that by generating none.

## Alternatives Considered

- **One generic instruction file for every tool:** loses native features (scoped rules, skills), and some tools ignore it.
- **Symlinking AGENTS.md to CLAUDE.md:** shares one file, but can't use per-tool mechanisms and breaks on Windows checkouts.

## Date

2026-10-01
