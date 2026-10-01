# Adding an Adapter

For maintainers: how to support another AI coding tool. An adapter teaches one more coding agent where to find the shared knowledge. It never contains engineering knowledge itself. To add an existing tool to a generated project, see the [User guide](user-guide.md#switch-tools-fallback) instead.

Related: [ADR-0003: Adapter pattern](decisions/adr-0003-adapter-pattern-for-coding-agents.md) · [Architecture: Adapters](architecture.md#adapters) · [Glossary](glossary.md)

## Contract

Create `adapters/<tool>/adapter.py` (and an empty `__init__.py`). The directory name is the `--tool` value.

```python
from bootstrap.compose import Composition, OutputFile

NAME = "<tool>"

def render(comp: Composition) -> list[OutputFile]:
    ...
```

`Composition` provides:

| Field | Content |
|-------|---------|
| `project_name` | From `--project-name` or the target directory name |
| `core_summary` | Operating-contract bullets |
| `core_docs` | `DocRef(title, path)` for each standard and governance document |
| `profiles` | `ProfileRef` with `id`, `name`, `description`, `summary`, `applies_to`, `doc`, `workflow_ids` |
| `workflows` | `WorkflowRef(id, description, path, owner)` for core and profile workflows |
| `doc_paths` | Every shared document the adapter must make reachable |

Rules:

- Return paths relative to the project root, using `/`.
- Never write under `docs/engineering/`. The neutral renderer owns it, and the bootstrap rejects it.
- Point to shared documents instead of copying their content. Keep the always-loaded entry file short.
- Output is deterministic: no timestamps, no environment lookups, stable ordering.
- Keep templates in `adapters/<tool>/templates/` and render them with `string.Template`.

## Checklist

1. Implement `render`.
2. Add tests next to `tests/test_adapters.py` covering native file format (frontmatter, required names), size budget, and determinism.
3. `tests/test_fallback.py` picks the adapter up automatically and must pass for it: every `doc_path`, summary bullet, and workflow description is reachable from its output.
4. Document the outputs in `docs/architecture.md` and personal configuration in `docs/personal-context.md`.

The bootstrap discovers adapters automatically. No registration is needed.
