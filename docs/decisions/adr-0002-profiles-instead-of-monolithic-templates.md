# ADR-0002: Profiles Instead of Monolithic Templates

## Status

Accepted

## Context

Projects combine technologies: a Python backend with RAG, a Python backend plus Next.js plus agents, and so on. One template per combination means N runtimes × M domains templates. Each would repeat the same Python or RAG guidance, and a fix would have to be applied to every copy.

## Decision

Guidance is split into small, independently composable **profiles** (`profiles/<category>/<name>/`). A project selects any set of them. Relationships are explicit:
- `requires` (auto-added dependencies, for example `fastapi` → `python-backend`);
- `conflicts` (combinations that are refused).

Profiles may add workflows but never patch or override core or other profiles. Tests compose every profile alone and in every pair. Validation rejects paragraphs duplicated across profiles and core.

## Consequences

- Each piece of guidance lives in one place. Profiles grow linearly, not combinatorially.
- New combinations need no new content, only a selection or a preset.
- Authors must decide boundaries carefully. Generic-versus-specific splits (for example `python-backend` vs `fastapi`) take judgment.
- Cross-profile nuance ("when RAG is used *with* FastAPI, do X") has no home in v0.1. It belongs in the project's `PROJECT.md`, or a future, narrower profile.

## Alternatives Considered

- **One template repository per stack combination:** simple to consume, but leads to combinatorial growth and duplicated content.
- **Profiles with section-level merging or overrides:** more flexible, but makes the final guidance hard to predict and lets one profile silently change another's content.

## Date

2026-10-01
