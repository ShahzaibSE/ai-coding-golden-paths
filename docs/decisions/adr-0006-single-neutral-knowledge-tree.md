# ADR-0006: Single Neutral Knowledge Tree in Generated Projects

## Status

Accepted

## Context

A neutral source repository ([ADR-0001](adr-0001-vendor-neutral-engineering-core.md)) is not enough by itself. If each adapter embedded the knowledge in its own files, a project set up for two tools would hold two copies that drift apart once edited, and switching tools would mean redefining standards.

## Decision

Every generated project gets one tool-neutral tree, `docs/engineering/`: standards, governance, workflows, profile guidance, an index, and a `PROJECT.md` seed. It is byte-identical whatever tools are selected. Adapter output (CLAUDE.md, `.claude/`, AGENTS.md) only summarizes the contract and points to or imports this tree. See [Architecture: Claude ↔ Codex fallback](../architecture.md#claude--codex-fallback).

## Consequences

- Tool fallback works: switching or adding a tool only adds entry points. `tests/test_fallback.py` proves this.
- Teams edit standards in one place. Developers without any AI tool can read them too.
- Agents may need an extra file read to reach the full guidance, which is mitigated by Claude Code imports and path-scoped rules.
- The project gains a `docs/engineering/` directory, which could collide with existing docs. Collisions are reported as conflicts and never overwritten ([ADR-0007](adr-0007-never-overwrite-user-files.md)).

## Alternatives Considered

- **Each adapter embeds the full knowledge:** fewer file reads, but duplicate copies and no clean fallback.
- **A hidden directory (`.golden-paths/`):** less clutter, but less discoverable for humans.

## Date

2026-10-01
