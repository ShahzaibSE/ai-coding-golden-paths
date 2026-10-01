"""Bootstrap a project with golden-path engineering guidance for one or more coding agents.

    python bootstrap/init.py --target ../my-app --tool claude --tool codex --preset fastapi-rag
    python bootstrap/init.py --target ../my-app --tool claude --profile runtime/python-backend --profile ai/rag
    python bootstrap/init.py --target ../my-app --tool codex          # add a tool to an initialized project

Safety: existing files are never overwritten unless this generator wrote them and they are
unchanged since. Generated files you have edited are kept as-is and reported. An existing file
this generator does not manage is a conflict, which aborts the run before anything is written.
Exit codes: 0 success, 1 invalid input, 2 file conflicts.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from bootstrap.compose import (
    GENERATOR,
    GENERATOR_VERSION,
    CompositionError,
    OutputFile,
    available_adapters,
    render_all,
    resolve_and_compose,
)
from bootstrap.validate import REPO_ROOT, ValidationError

MANIFEST = ".golden-paths.yaml"

CREATE, UPDATE, UNCHANGED, KEEP, CONFLICT = "create", "update", "unchanged", "keep", "conflict"


class InitError(Exception):
    """Invalid input or target state; nothing has been written."""


@dataclass(frozen=True)
class Action:
    kind: str
    file: OutputFile
    reason: str = ""


@dataclass
class Result:
    actions: list[Action]
    notes: list[str]
    written: bool

    @property
    def conflicts(self) -> list[Action]:
        return [a for a in self.actions if a.kind == CONFLICT]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest(target: Path) -> dict | None:
    path = target / MANIFEST
    if not path.exists():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise InitError(f"{MANIFEST} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict) or data.get("generator") != GENERATOR:
        raise InitError(f"{MANIFEST} exists but was not written by {GENERATOR}; refusing to continue")
    return data


def safe_destination(target: Path, rel: str) -> Path:
    pure = PurePosixPath(rel)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise InitError(f"unsafe output path: {rel}")
    dest = target / Path(*pure.parts)
    if not dest.resolve().is_relative_to(target.resolve()):
        raise InitError(f"output path escapes the target (symlink?): {rel}")
    return dest


def classify(target: Path, files: list[OutputFile], recorded: dict[str, str]) -> list[Action]:
    actions = []
    for f in files:
        dest = safe_destination(target, f.path)
        if not dest.exists():
            actions.append(Action(CREATE, f))
            continue
        if not dest.is_file():
            actions.append(Action(CONFLICT, f, "exists and is not a regular file"))
            continue
        current = dest.read_bytes()
        if f.seed_only:
            actions.append(Action(KEEP, f, "project-owned seed; never regenerated"))
        elif current == f.content.encode("utf-8"):
            actions.append(Action(UNCHANGED, f))
        elif f.path not in recorded:
            actions.append(Action(CONFLICT, f, "exists and is not managed by this generator"))
        elif sha256(current) != recorded[f.path]:
            actions.append(Action(KEEP, f, "edited since it was generated; your version is kept"))
        else:
            actions.append(Action(UPDATE, f))
    return actions


def write_atomic(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=f".{dest.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, dest)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def run(
    target: Path,
    tools: list[str],
    *,
    preset: str | None = None,
    profiles: list[str] | None = None,
    project_name: str | None = None,
    dry_run: bool = False,
    root: Path = REPO_ROOT,
) -> Result:
    """Plan and (unless dry_run or conflicted) apply generation. Raises InitError on bad input."""
    target = target.expanduser().absolute()
    if target.exists() and not target.is_dir():
        raise InitError(f"target is not a directory: {target}")
    manifest = load_manifest(target) if target.exists() else None

    known = available_adapters(root)
    unknown = [t for t in tools if t not in known]
    if unknown:
        raise InitError(f"unknown tool(s): {', '.join(unknown)}. Available: {', '.join(known)}")

    notes: list[str] = []
    recorded_files: dict[str, str] = {}
    if manifest:
        recorded_tools = list(manifest.get("tools", []))
        recorded_profiles = [p["id"] for p in manifest.get("profiles", [])]
        recorded_files = dict(manifest.get("files", {}))
        tools = sorted(set(recorded_tools) | set(tools))
        if not preset and not profiles:
            preset = manifest.get("preset")
            profiles = [] if preset else recorded_profiles
            notes.append(f"reusing recorded selection from {MANIFEST}")
        project_name = project_name or manifest.get("project_name")
    if not tools:
        raise InitError("select at least one --tool")
    tools = sorted(set(tools))
    project_name = project_name or target.name

    try:
        comp, resolve_notes = resolve_and_compose(project_name, preset=preset, profiles=profiles, root=root)
        files = render_all(comp, tools, root)
    except (CompositionError, ValidationError) as exc:
        raise InitError(str(exc)) from exc
    notes.extend(resolve_notes)

    selected = [p.id for p in comp.profiles]
    if manifest and selected != recorded_profiles:
        raise InitError(
            f"profile selection {selected} differs from the recorded {recorded_profiles}; "
            "changing profiles of an initialized project is not supported in v0.1"
        )

    actions = classify(target, files, recorded_files)
    result = Result(actions, notes, written=False)
    if result.conflicts or dry_run:
        return result

    for action in actions:
        if action.kind in (CREATE, UPDATE):
            write_atomic(safe_destination(target, action.file.path), action.file.content.encode("utf-8"))

    hashes = dict(recorded_files)
    for action in actions:
        if action.file.seed_only:
            hashes.pop(action.file.path, None)  # seeds belong to the project once written
        elif action.kind in (CREATE, UPDATE, UNCHANGED):
            hashes[action.file.path] = sha256(action.file.content.encode("utf-8"))
    new_manifest = {
        "generator": GENERATOR,
        "generator_version": GENERATOR_VERSION,
        "project_name": project_name,
        "preset": comp.preset,
        "profiles": [{"id": p.id, "version": p.version} for p in comp.profiles],
        "tools": tools,
        "files": dict(sorted(hashes.items())),
    }
    header = (
        f"# Written by {GENERATOR}. Records what was generated so re-runs never overwrite your edits.\n"
        "# Nothing reads this at runtime; it is safe to commit.\n"
    )
    manifest_bytes = (header + yaml.safe_dump(new_manifest, sort_keys=False)).encode("utf-8")
    manifest_path = target / MANIFEST
    if not manifest_path.exists() or manifest_path.read_bytes() != manifest_bytes:
        write_atomic(manifest_path, manifest_bytes)
    result.written = True
    return result


def summarize(result: Result, dry_run: bool) -> str:
    lines = [f"note: {n}" for n in result.notes]
    order = [CONFLICT, CREATE, UPDATE, KEEP, UNCHANGED]
    counts = {k: 0 for k in order}
    for kind in order:
        for a in sorted((a for a in result.actions if a.kind == kind), key=lambda a: a.file.path):
            counts[kind] += 1
            suffix = f"  ({a.reason})" if a.reason else ""
            lines.append(f"  {kind:<10} {a.file.path}{suffix}")
    lines.append(", ".join(f"{counts[k]} {k}" for k in order if counts[k]))
    if result.conflicts:
        lines.append(
            "aborted: nothing was written. Move, rename, or merge the conflicting files by hand, then re-run."
        )
    elif dry_run:
        lines.append("dry run: nothing was written.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", required=True, type=Path, help="project directory to initialize")
    parser.add_argument("--tool", action="append", default=[], help=f"coding agent adapter ({', '.join(available_adapters())}); repeatable")
    parser.add_argument("--preset", help="preset name from presets/")
    parser.add_argument("--profile", action="append", default=[], help="profile id like runtime/python-backend; repeatable")
    parser.add_argument("--project-name", help="defaults to the recorded name or the target directory name")
    parser.add_argument("--dry-run", action="store_true", help="show the change summary without writing")
    args = parser.parse_args(argv)

    try:
        result = run(
            args.target,
            args.tool,
            preset=args.preset,
            profiles=args.profile,
            project_name=args.project_name,
            dry_run=args.dry_run,
        )
    except InitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(summarize(result, args.dry_run))
    return 2 if result.conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
