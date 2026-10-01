"""Resolve a profile selection and build the tool-neutral Composition that adapters render."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from pathlib import Path

from bootstrap.validate import (
    REPO_ROOT,
    Core,
    Profile,
    discover_presets,
    discover_profiles,
    load_core,
)

GENERATOR = "ai-coding-golden-paths"
GENERATOR_VERSION = "0.1.0"
DOCS_ROOT = "docs/engineering"
PROJECT_DOC = f"{DOCS_ROOT}/PROJECT.md"


class CompositionError(Exception):
    """Raised when a selection cannot be composed safely."""


@dataclass(frozen=True)
class OutputFile:
    path: str  # POSIX path relative to the target project
    content: str
    seed_only: bool = False  # written once, never updated afterwards


@dataclass(frozen=True)
class DocRef:
    title: str
    path: str  # generated path under docs/engineering/
    source: Path


@dataclass(frozen=True)
class WorkflowRef:
    id: str
    description: str
    path: str
    source: Path
    owner: str  # "core" or a profile id


@dataclass(frozen=True)
class ProfileRef:
    id: str
    name: str
    version: str
    description: str
    summary: tuple[str, ...]
    applies_to: tuple[str, ...]
    doc: DocRef
    workflow_ids: tuple[str, ...]


@dataclass(frozen=True)
class Composition:
    project_name: str
    preset: str | None
    core_version: str
    core_summary: tuple[str, ...]
    core_docs: tuple[DocRef, ...]
    profiles: tuple[ProfileRef, ...]
    workflows: tuple[WorkflowRef, ...]

    @property
    def doc_paths(self) -> tuple[str, ...]:
        """Every neutral knowledge document an adapter must make reachable."""
        return (
            tuple(d.path for d in self.core_docs)
            + tuple(p.doc.path for p in self.profiles)
            + tuple(w.path for w in self.workflows)
        )


def doc_title(source: Path) -> str:
    for line in source.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return source.stem.replace("-", " ").title()


def resolve_selection(
    available: dict[str, Profile], preset_profiles: list[str], explicit: list[str]
) -> tuple[list[str], list[str]]:
    """Return (ordered profile ids, human-readable notes).

    Order: preset profiles, then explicit profiles, deduplicated (first wins);
    missing `requires` are inserted before their first dependent.
    """
    notes: list[str] = []
    requested: list[str] = []
    for pid in list(preset_profiles) + list(explicit):
        if pid not in available:
            raise CompositionError(
                f"unknown profile '{pid}'. Available: {', '.join(sorted(available))}"
            )
        if pid in requested:
            notes.append(f"profile '{pid}' selected more than once; using it once")
            continue
        requested.append(pid)

    resolved: list[str] = []

    def add(pid: str, chain: tuple[str, ...]) -> None:
        if pid in chain:
            raise CompositionError(f"circular 'requires': {' -> '.join(chain + (pid,))}")
        if pid in resolved:
            return
        for dep in available[pid].requires:
            if dep not in available:
                raise CompositionError(f"profile '{pid}' requires unknown profile '{dep}'")
            if dep not in resolved and dep not in requested:
                notes.append(f"added '{dep}' (required by '{pid}')")
            add(dep, chain + (pid,))
        resolved.append(pid)

    for pid in requested:
        add(pid, ())
    return resolved, notes


def check_conflicts(core: Core, profiles: list[Profile]) -> None:
    ids = {p.id for p in profiles}
    for profile in profiles:
        for other in profile.conflicts:
            if other in ids:
                raise CompositionError(f"profile '{profile.id}' declares a conflict with '{other}'")

    owners: dict[str, str] = {wf.id: "core" for wf in core.workflows}
    for profile in profiles:
        for wf in profile.workflows:
            if wf.id in owners:
                raise CompositionError(
                    f"workflow '{wf.id}' is provided by both {owners[wf.id]} and {profile.id}; "
                    "profiles may add workflows but never replace one"
                )
            owners[wf.id] = profile.id


def compose(
    project_name: str,
    profile_ids: list[str],
    *,
    preset: str | None = None,
    root: Path = REPO_ROOT,
) -> Composition:
    """Build a Composition from already-resolved profile ids."""
    core = load_core(root / "core")
    available = discover_profiles(root / "profiles")
    missing = [pid for pid in profile_ids if pid not in available]
    if missing:
        raise CompositionError(f"unknown profile(s): {', '.join(missing)}")
    profiles = [available[pid] for pid in profile_ids]
    check_conflicts(core, profiles)

    core_docs = tuple(DocRef(doc_title(src), f"{DOCS_ROOT}/{rel}", src) for rel, src in core.documents)
    workflows = [
        WorkflowRef(wf.id, wf.description, f"{DOCS_ROOT}/workflows/{wf.id}.md", wf.source, "core")
        for wf in core.workflows
    ]
    profile_refs = []
    for p in profiles:
        doc = DocRef(doc_title(p.guidance), f"{DOCS_ROOT}/profiles/{p.name}.md", p.guidance)
        profile_refs.append(
            ProfileRef(p.id, p.name, p.version, p.description, p.summary, p.applies_to, doc,
                       tuple(wf.id for wf in p.workflows))
        )
        workflows += [
            WorkflowRef(wf.id, wf.description, f"{DOCS_ROOT}/workflows/{wf.id}.md", wf.source, p.id)
            for wf in p.workflows
        ]

    return Composition(
        project_name=project_name,
        preset=preset,
        core_version=core.version,
        core_summary=core.summary,
        core_docs=core_docs,
        profiles=tuple(profile_refs),
        workflows=tuple(workflows),
    )


def resolve_and_compose(
    project_name: str,
    *,
    preset: str | None = None,
    profiles: list[str] | None = None,
    root: Path = REPO_ROOT,
) -> tuple[Composition, list[str]]:
    """Convenience: resolve preset + explicit profiles, then compose."""
    available = discover_profiles(root / "profiles")
    preset_profiles: list[str] = []
    if preset:
        presets = discover_presets(root / "presets")
        if preset not in presets:
            raise CompositionError(f"unknown preset '{preset}'. Available: {', '.join(sorted(presets))}")
        preset_profiles = list(presets[preset].profiles)
    ids, notes = resolve_selection(available, preset_profiles, profiles or [])
    if not ids:
        raise CompositionError("no profiles selected; pass --preset and/or --profile")
    return compose(project_name, ids, preset=preset, root=root), notes


# --- adapters -----------------------------------------------------------------

ADAPTER_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def available_adapters(root: Path = REPO_ROOT) -> list[str]:
    return sorted(
        d.name for d in (root / "adapters").iterdir()
        if d.is_dir() and ADAPTER_NAME.match(d.name) and (d / "adapter.py").is_file()
    )


def load_adapter(name: str, root: Path = REPO_ROOT):
    if name not in available_adapters(root):
        raise CompositionError(f"unknown tool '{name}'. Available: {', '.join(available_adapters(root))}")
    return importlib.import_module(f"adapters.{name}.adapter")


def render_all(comp: Composition, tools: list[str], root: Path = REPO_ROOT) -> list[OutputFile]:
    """Render neutral docs plus each tool's entry points; reject path collisions."""
    from bootstrap import neutral

    outputs = list(neutral.render(comp))
    for tool in tools:
        adapter = load_adapter(tool, root)
        files = adapter.render(comp)
        for f in files:
            if f.path == DOCS_ROOT or f.path.startswith(DOCS_ROOT + "/"):
                raise CompositionError(f"adapter '{tool}' may not write shared docs ({f.path})")
        outputs.extend(files)

    seen: dict[str, str] = {}
    for f in outputs:
        key = f.path.lower()  # case-insensitive filesystems
        if key in seen:
            raise CompositionError(f"two outputs claim the same path: {f.path}")
        seen[key] = f.path
    return sorted(outputs, key=lambda f: f.path)

