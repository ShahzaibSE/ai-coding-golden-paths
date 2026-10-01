# Personal Context

What is shared and committed, and what stays on a developer's machine. Generated configuration is shared by the whole team and committed. Personal configuration must stay out of it.

Related: [User guide](user-guide.md) · [Glossary](glossary.md)

**Personal** (keep out of generated files, profiles, and presets):
- local paths (skill labs, scratch directories, other checkouts)
- local sandbox or staging URLs and personal accounts
- machine-specific tooling (shell aliases, local model servers, editor settings)
- individual workflow preferences (verbosity, commit style beyond team rules, preferred tools)

**Shared** (belongs in the project, usually `docs/engineering/PROJECT.md`): team commands, architecture, conventions, and decisions everyone must follow.

## Claude Code

| File | Scope | Committed? |
|------|-------|-----------|
| `~/.claude/CLAUDE.md` | You, all projects | No (home directory) |
| `~/.claude/rules/*.md` | You, all projects; supports `paths:` scoping | No |
| `CLAUDE.local.md` (project root) | You, this project | No: add it to `.gitignore` |
| `.claude/settings.local.json` | Your permissions and env for this project | No |

Personal instructions load alongside the generated `CLAUDE.md`. They do not replace it. Avoid contradicting team rules: when instructions conflict, the agent may follow either.

Note: a `CLAUDE.local.md` counts as a CLAUDE.md for Claude Code's AGENTS.md fallback. Since generated projects ship a `CLAUDE.md` anyway, this changes nothing here.

## Codex

| File | Scope | Committed? |
|------|-------|-----------|
| `~/.codex/AGENTS.md` (under `$CODEX_HOME` if set) | You, all projects | No |
| `~/.codex/config.toml` | Your model, sandbox, and approval settings | No |

Codex merges user-level instructions with the project's `AGENTS.md`. Check the current Codex documentation for override files and precedence, since these details have changed between releases.

## Rules for contributors to this repository

- Never put personal paths, URLs, accounts, or preferences in `core/`, `profiles/`, or `presets/`. `python bootstrap/validate.py` rejects absolute home-directory paths, but it cannot catch everything.
- If a preference is useful to the whole team, propose it as a profile or core change, written in neutral language.
