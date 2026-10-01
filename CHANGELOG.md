# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow semantic versioning.

## [0.1.0] - 2026-10-01

### Added
- Vendor-neutral core: engineering, testing, security, and git standards; implementation and code-review workflows; privacy baseline.
- Profiles: `runtime/python-backend`, `runtime/fastapi`, `runtime/nextjs`, `ai/rag` (with retrieval-evaluation workflow), `ai/agentic-ai` (with agent-evaluation workflow).
- Presets: `fastapi-rag`, `fullstack-agentic-ai`.
- Adapters: Claude Code (`CLAUDE.md`, path-scoped rules, skills, code-reviewer agent) and Codex (`AGENTS.md`).
- `bootstrap/init.py` with presets or explicit profiles, multiple tools per run, dry-run, change summary, idempotent re-runs, and protection of existing and edited files.
- `bootstrap/validate.py` repository lint: contract shape, vendor neutrality, machine paths, duplicate content.
- Tests for composition, conflicts, adapters, bootstrap safety, and Claude ↔ Codex fallback equivalence.
- Documentation: user guide, creating-a-profile guide, glossary, and architecture decision records (ADR-0001 to ADR-0007), with a link-check test.
