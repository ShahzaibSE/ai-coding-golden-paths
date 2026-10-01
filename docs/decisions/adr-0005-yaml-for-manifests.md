# ADR-0005: YAML for Manifests

## Status

Accepted

## Context

Profiles, core, presets, and the generated project's `.golden-paths.yaml` need small, human-edited metadata files. The format must support comments and lists, be readable in code review, and stay easy for maintainers to write.

## Decision

All manifests use YAML, parsed with PyYAML (`yaml.safe_load`). PyYAML is the bootstrap's only runtime dependency. Validation is plain Python in `bootstrap/validate.py`, not JSON Schema, so the contract has one definition. Generated projects do not depend on PyYAML or on this repository.

## Consequences

- Readable, commentable manifests that match common practice for this kind of configuration.
- One small, ubiquitous dependency for the bootstrap only.
- YAML has edge cases (implicit typing, for example `no` → false). These are acceptable because the schemas are tiny and validation checks types.
- **This can be revisited.** If the dependency becomes a burden, TOML via the standard-library `tomllib` (read) is the likely replacement. Only the loaders in `validate.py` and `init.py` would change.

## Alternatives Considered

- **JSON:** no dependency, but no comments and noisier to hand-edit.
- **TOML:** reading needs no dependency, but writing the target manifest would need one, and the format departs from the original specification.
- **JSON Schema + jsonschema:** a formal schema, but adds a dependency and a second definition of the contract.

## Date

2026-10-01
