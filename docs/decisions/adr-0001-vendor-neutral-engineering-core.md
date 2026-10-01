# ADR-0001: Vendor-Neutral Engineering Core

## Status

Accepted

## Context

Engineering standards (testing, security, review, git hygiene) change slowly. AI coding tools and their configuration formats change quickly. Teams use more than one tool at once. Standards written directly into one tool's instruction file get copied into other tools' files, drift apart, and must be rewritten when the team switches tools.

## Decision

All engineering knowledge in `core/` and `profiles/` is written in agent-neutral language. It does not mention any coding agent, instruction-file name, or model provider. `bootstrap/validate.py` enforces this by rejecting vendor terms and absolute machine paths in shared content. Tool-specific wording exists only in adapters ([ADR-0003](adr-0003-adapter-pattern-for-coding-agents.md)).

## Consequences

- One source of truth serves every current and future tool.
- Standards can be reviewed by people who don't use a given tool.
- The lint is a blunt instrument. A legitimate mention of a vendor name, for example a provider in a RAG profile, must be phrased generically or recorded in the project's own `PROJECT.md`.
- Some tool-specific capability (for example hooks) cannot be expressed in the core and has to be added per adapter.

## Alternatives Considered

- **Write standards directly in CLAUDE.md or AGENTS.md:** fastest to start, but duplicates content per tool and ties the knowledge to one vendor.
- **Neutral core without enforcement:** relies on reviewers noticing leaks; rejected because leaks are easy to miss.

## Date

2026-10-01
