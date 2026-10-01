import shutil
from pathlib import Path

import pytest

from bootstrap.validate import REPO_ROOT


def write_profile(root: Path, pid: str, **fields) -> Path:
    """Create a minimal valid profile under root/profiles; fields override profile.yaml keys."""
    category, name = pid.split("/")
    pdir = root / "profiles" / category / name
    pdir.mkdir(parents=True)
    workflows = fields.pop("workflows", [])
    for wf in workflows:
        (pdir / wf["file"]).parent.mkdir(parents=True, exist_ok=True)
        (pdir / wf["file"]).write_text(f"# {wf['id']}\n\nSteps unique to {pid} {wf['id']}.\n")
    data = {"name": name, "version": "0.1.0", "category": category, "description": f"Test profile {pid}"}
    data.update(fields)
    if workflows:
        data["workflows"] = workflows
    import yaml

    (pdir / "profile.yaml").write_text(yaml.safe_dump(data))
    (pdir / "guidance.md").write_text(f"# {name}\n\nGuidance unique to the {pid} test profile.\n")
    return pdir


@pytest.fixture
def repo_copy(tmp_path: Path) -> Path:
    """A disposable copy of the repository content (core, profiles, presets, adapters)."""
    root = tmp_path / "repo"
    for part in ("core", "profiles", "presets", "adapters"):
        shutil.copytree(REPO_ROOT / part, root / part, ignore=shutil.ignore_patterns("__pycache__"))
    return root


def tree(path: Path) -> dict[str, bytes]:
    """Map of relative POSIX path -> bytes for every file under path."""
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in sorted(path.rglob("*")) if p.is_file()}
