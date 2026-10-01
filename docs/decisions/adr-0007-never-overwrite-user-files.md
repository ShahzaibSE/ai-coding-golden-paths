# ADR-0007: Never Overwrite User Files

## Status

Accepted

## Context

The bootstrap writes into real projects that may already have a CLAUDE.md, AGENTS.md, or docs, and whose teams will edit the generated files. Re-running the generator (to add a tool, or after an upgrade) must be safe. Silently losing a team's edits would make the tool untrustworthy.

## Decision

The target manifest `.golden-paths.yaml` records the SHA-256 of every file the generator wrote. On each run:
- untouched generated files may be updated;
- edited generated files are kept and reported;
- the `PROJECT.md` seed is never regenerated;
- any existing file the generator did not write is a conflict that aborts the whole run before anything is written (exit 2).

There is no `--force` in v0.1. `--dry-run` shows the full plan. See [Architecture: Safe writing](../architecture.md#safe-writing).

## Consequences

- Re-runs are safe and idempotent, and adding a tool to a customized project works.
- Conflicts must be resolved by hand, by moving or merging the file.
- Edited files no longer receive generator improvements automatically. Teams merge them by hand if they want them.

## Alternatives Considered

- **Overwrite with `.bak` backups:** convenient, but easy to lose edits unnoticed.
- **Interactive prompts per file:** not scriptable, and results depend on who runs it.
- **Write `.new` files beside conflicts:** leaves clutter, and only defers the decision.

## Date

2026-10-01
