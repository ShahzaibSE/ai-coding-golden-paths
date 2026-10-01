# Architecture Decisions

Architecture Decision Records (ADRs) explain *why* the system is built the way it is. [Architecture](../architecture.md) explains *how*.

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](adr-0001-vendor-neutral-engineering-core.md) | Vendor-neutral engineering core | Accepted |
| [0002](adr-0002-profiles-instead-of-monolithic-templates.md) | Profiles instead of monolithic templates | Accepted |
| [0003](adr-0003-adapter-pattern-for-coding-agents.md) | Adapter pattern for coding agents | Accepted |
| [0004](adr-0004-presets-are-composition-only.md) | Presets are composition only | Accepted |
| [0005](adr-0005-yaml-for-manifests.md) | YAML for manifests | Accepted |
| [0006](adr-0006-single-neutral-knowledge-tree.md) | Single neutral knowledge tree in generated projects | Accepted |
| [0007](adr-0007-never-overwrite-user-files.md) | Never overwrite user files | Accepted |

## Adding an ADR

1. Copy [the template](adr-0000-template.md) to `adr-NNNN-short-title.md` using the next number.
2. Keep it short: context, decision, consequences, alternatives.
3. Never rewrite an accepted ADR's decision. Supersede it with a new ADR and set the old one's status to Superseded.
4. Add it to the table above.
