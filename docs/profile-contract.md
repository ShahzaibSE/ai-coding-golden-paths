# Profile Contract

The authoritative rules every profile and preset must satisfy. `bootstrap/validate.py` enforces them. For the step-by-step procedure, see [Creating a profile](creating-a-profile.md).

Related: [Glossary](glossary.md) · [ADR-0002: Profiles](decisions/adr-0002-profiles-instead-of-monolithic-templates.md) · [ADR-0004: Presets](decisions/adr-0004-presets-are-composition-only.md)

A profile is reusable guidance for one technology or domain. It lives at `profiles/<category>/<name>/` and its id is `<category>/<name>`.

## Files

```
profiles/ai/rag/
├── profile.yaml        # required: metadata and adapter inputs
├── guidance.md         # required: the full guidance, neutral language
└── workflows/          # optional: new procedures this profile adds
    └── retrieval-evaluation.md
```

## `profile.yaml`

```yaml
name: rag                          # required; equals the directory name; unique across categories
version: 0.1.0                     # required; semver
category: ai                       # required; equals the parent directory
description: One line.             # required
summary:                           # optional; 2-6 short bullets copied into every entry file
  - Answers are grounded only in retrieved evidence.
applies_to:                        # optional; file globs where this guidance matters
  - "**/*.py"
workflows:                         # optional; procedures this profile adds
  - id: retrieval-evaluation       # unique across core and all profiles
    file: workflows/retrieval-evaluation.md
    description: When to use it (used for skill descriptions and workflow lists).
requires: [runtime/python-backend] # optional; auto-added when this profile is selected
conflicts: []                      # optional; profiles that cannot be combined with this one
```

Unknown keys are rejected.

Every field is tool-neutral. Adapters decide how to render each one: `applies_to` becomes a path-scoped rule for Claude Code and an "Applies to" note in `AGENTS.md`, and `workflows` become skills or linked documents.

## Rules

1. **No core restatement.** If a sentence would be true for a project without this profile, it belongs in `core/`. Validation fails when any non-trivial paragraph appears in two places.
2. **Vendor-neutral.** No coding-agent names, instruction-file names, or model-provider names. Validation enforces this.
3. **No machine specifics.** No absolute paths, hostnames, credentials, or personal preferences.
4. **Additive only.** A profile may add workflows. It may not replace or patch a core workflow or another profile's content. If two profiles genuinely cannot coexist, declare `conflicts`.
5. **Composable alone.** A profile works with only its `requires`. Tests compose every profile alone and in every pair.
6. **Actionable and short.** Write rules an engineer can check in review, not tutorials. Aim for 40-120 lines.

## Presets

A preset is a convenience name for a list of profiles. It may contain only `name`, `description`, and `profiles`, and its `name` must equal the file name:

```yaml
name: fastapi-rag
description: Python FastAPI service with retrieval-augmented generation.
profiles: [runtime/python-backend, runtime/fastapi, ai/rag]
```
