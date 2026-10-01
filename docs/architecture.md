# Architecture

How the system is built. The reasons for each decision are recorded in [Architecture decisions](decisions/README.md); terms are defined in the [Glossary](glossary.md).

Related: [User guide](user-guide.md) · [Profile contract](profile-contract.md) · [Adding an adapter](adding-an-adapter.md)

```
core (always)  +  profiles (selected)  +  preset (a named selection)
        │
        ▼  bootstrap/compose.py — resolve, check conflicts, build a Composition
        │
        ├─► bootstrap/neutral.py ─► docs/engineering/**        (one shared knowledge tree)
        └─► adapters/<tool>/      ─► CLAUDE.md, .claude/** │ AGENTS.md   (thin entry points)
```

## Layers

| Layer | Location | Owns | Must not |
|-------|----------|------|----------|
| Core | `core/` | Universal standards, workflows, privacy baseline | Mention a vendor, a stack, or a machine path |
| Profiles | `profiles/<category>/<name>/` | Technology- or domain-specific guidance and procedures | Restate core, override another profile, mention a vendor |
| Presets | `presets/*.yaml` | A named list of profile ids | Contain any guidance |
| Adapters | `adapters/<tool>/` | How one coding agent discovers instructions | Contain engineering knowledge, write under `docs/engineering/` |
| Bootstrap | `bootstrap/` | Validation, resolution, rendering, safe writing | Know about any specific tool |

`bootstrap/validate.py` enforces the content rules: contract shape, vendor-neutral language, no absolute paths, and no paragraph duplicated across core and profiles. To decide which layer content belongs in, see [Creating a profile](creating-a-profile.md#core--profile--preset--adapter).

Rationale: [ADR-0001](decisions/adr-0001-vendor-neutral-engineering-core.md), [ADR-0002](decisions/adr-0002-profiles-instead-of-monolithic-templates.md), [ADR-0004](decisions/adr-0004-presets-are-composition-only.md), [ADR-0005](decisions/adr-0005-yaml-for-manifests.md).

## The generated project

```
my-app/
├── docs/engineering/          # shared by every tool; identical whatever tools are selected
│   ├── README.md              # index
│   ├── PROJECT.md             # seed: architecture, commands, decisions (yours to fill in)
│   ├── standards/  governance/  workflows/  profiles/
├── CLAUDE.md, .claude/        # only with --tool claude
├── AGENTS.md                  # only with --tool codex
└── .golden-paths.yaml         # record of selection + hashes of generated files
```

Generated projects have no runtime dependency on this repository. Every file is owned by the project and can be edited. `.golden-paths.yaml` exists only so that re-running the generator can tell its own unmodified files apart from your edits.

Rationale: [ADR-0006](decisions/adr-0006-single-neutral-knowledge-tree.md).

## Adapters

Rationale: [ADR-0003](decisions/adr-0003-adapter-pattern-for-coding-agents.md). Writing a new adapter: [Adding an adapter](adding-an-adapter.md).

### Claude Code (`adapters/claude/`)

| Output | Purpose |
|--------|---------|
| `CLAUDE.md` | Concise, always-loaded contract: imports `PROJECT.md`, lists core summary bullets, standards, active profiles, skills |
| `.claude/rules/<profile>.md` | One per profile with `applies_to` globs. `paths:` frontmatter makes it load only when matching files are touched. Points to and imports the profile guidance (`@../../docs/...`, because imports resolve relative to the rule file) |
| `.claude/skills/<workflow>/SKILL.md` | One per workflow; directs the agent to the neutral workflow document |
| `.claude/agents/code-reviewer.md` | Read-only reviewer that follows the code-review workflow |

**Workflow to skill to slash command.** A workflow is written once in `core/workflows/` and copied to `docs/engineering/workflows/`. The adapter wraps it in a thin skill whose name is the workflow id, which gives the `/<id>` command. The skill body only points at the neutral document. Claude-specific behavior stays in the adapter: for example, `git-commit` and `git-release` change repository state, so their skills set `disable-model-invocation` and run only when invoked explicitly. Codex lists the same workflows in `AGENTS.md`. See [ADR-0003](decisions/adr-0003-adapter-pattern-for-coding-agents.md) and [ADR-0006](decisions/adr-0006-single-neutral-knowledge-tree.md).

No hooks are generated in v0.1: no candidate was both deterministic and toolchain-neutral, and Codex has no equivalent mechanism.

### Codex (`adapters/codex/`)

A single root `AGENTS.md`: a project map and operating contract that links every standard, profile, and workflow in `docs/engineering/`. Nested `AGENTS.md` files and `.agent/PLANS.md` are not generated in v0.1. The implementation workflow already contains the execution-plan guidance, and nested files would need a profile-to-directory mapping (planned).

## Claude ↔ Codex fallback

The engineering knowledge exists exactly once in a generated project, in `docs/engineering/`. Adapters only decide *how* an agent finds it. Consequently:

- Initialize with `--tool claude --tool codex` and both agents read the same standards, profiles, and workflows.
- Initialize with one tool and add the other later with `--tool <other>`. The recorded selection is reused, and only the new entry points are created.
- Architecture and commands live in `PROJECT.md`, which both entry points load or link.

Note: when both `CLAUDE.md` and `AGENTS.md` exist, Claude Code reads `CLAUDE.md` by default. The generated `CLAUDE.md` is complete on its own, so this is the intended behavior.

`tests/test_fallback.py` proves the property:
- `docs/engineering/` is byte-identical for claude, codex, or both.
- Every shared document, summary bullet, and workflow is reachable from each tool's entry points.
- Adding a tool later produces exactly the same tree as generating both at once.

## Composition and conflicts

Nothing is merged. Each source document becomes exactly one output file. Generation stops with an error when:

- a selected profile declares a `conflict` with another selected profile;
- two sources provide the same workflow id (profiles may add workflows, never replace one);
- a profile `requires` an unknown profile, or requirements are circular;
- two outputs claim the same path, or an adapter tries to write shared docs.

## Safe writing

| Situation | Action |
|-----------|--------|
| File does not exist | `create` |
| Identical content | `unchanged` |
| Generated earlier, untouched since | `update` |
| Generated earlier, edited since | `keep`: your version stays |
| `docs/engineering/PROJECT.md` exists | `keep`: it is a seed, never regenerated |
| Exists but not generated by this tool | `conflict`: whole run aborts, nothing written, exit 2 |

`--dry-run` prints the same plan without writing. Output paths are checked to stay inside the target, including through symlinks. Re-running with the same inputs is a no-op.

Rationale: [ADR-0007](decisions/adr-0007-never-overwrite-user-files.md).

## v0.1 limits

- Changing the profile set of an initialized project is refused. Removing a tool is manual: delete its files and its entry under `tools:` in `.golden-paths.yaml`.
- There is no `--force`. Resolve conflicts by moving or merging files by hand.
