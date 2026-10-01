"""Load and validate core, profiles, and presets.

Also usable as a repository lint:  python bootstrap/validate.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")

PROFILE_REQUIRED = {"name", "version", "category", "description"}
PROFILE_OPTIONAL = {"summary", "applies_to", "workflows", "requires", "conflicts"}
CORE_REQUIRED = PROFILE_REQUIRED | {"documents"}
CORE_OPTIONAL = {"summary", "workflows"}
PRESET_KEYS = {"name", "description", "profiles"}
WORKFLOW_KEYS = {"id", "file", "description"}

# Shared knowledge must stay vendor-neutral and machine-independent.
VENDOR_TERMS = re.compile(
    r"\b(Claude|Codex|Anthropic|OpenAI|Copilot|Gemini)\b|CLAUDE\.md|AGENTS\.md"
)
ABSOLUTE_PATHS = re.compile(r"(/Users/|/home/|[A-Za-z]:\\)")
MIN_DUPLICATE_PARAGRAPH = 60


class ValidationError(Exception):
    """Raised when repository content does not satisfy the contract."""


@dataclass(frozen=True)
class Workflow:
    id: str
    description: str
    source: Path


@dataclass(frozen=True)
class Profile:
    id: str  # "<category>/<name>"
    name: str
    version: str
    category: str
    description: str
    summary: tuple[str, ...]
    applies_to: tuple[str, ...]
    workflows: tuple[Workflow, ...]
    requires: tuple[str, ...]
    conflicts: tuple[str, ...]
    guidance: Path


@dataclass(frozen=True)
class Core:
    version: str
    description: str
    summary: tuple[str, ...]
    documents: tuple[tuple[str, Path], ...]  # (relative path, source file)
    workflows: tuple[Workflow, ...]


@dataclass(frozen=True)
class Preset:
    name: str
    description: str
    profiles: tuple[str, ...]


def load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValidationError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: expected a mapping at the top level")
    return data


def _check_keys(path: Path, data: dict, required: set, optional: set) -> None:
    missing = required - data.keys()
    if missing:
        raise ValidationError(f"{path}: missing required keys: {', '.join(sorted(missing))}")
    unknown = data.keys() - required - optional
    if unknown:
        raise ValidationError(f"{path}: unknown keys: {', '.join(sorted(unknown))}")
    for key in PROFILE_REQUIRED:
        if not isinstance(data[key], str) or not data[key].strip():
            raise ValidationError(f"{path}: '{key}' must be a non-empty string")
    if not SEMVER.match(data["version"]):
        raise ValidationError(f"{path}: version '{data['version']}' is not semver (X.Y.Z)")


def _str_list(path: Path, data: dict, key: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        raise ValidationError(f"{path}: '{key}' must be a list of non-empty strings")
    return tuple(value)


def _existing_file(path: Path, base: Path, rel: str) -> Path:
    source = (base / rel).resolve()
    if not source.is_relative_to(base.resolve()):
        raise ValidationError(f"{path}: '{rel}' points outside {base}")
    if not source.is_file() or not source.read_text(encoding="utf-8").strip():
        raise ValidationError(f"{path}: '{rel}' is missing or empty")
    return source


def _workflows(path: Path, data: dict, base: Path) -> tuple[Workflow, ...]:
    raw = data.get("workflows", [])
    if not isinstance(raw, list):
        raise ValidationError(f"{path}: 'workflows' must be a list")
    result = []
    for entry in raw:
        if not isinstance(entry, dict) or set(entry) != WORKFLOW_KEYS:
            raise ValidationError(f"{path}: each workflow needs exactly {sorted(WORKFLOW_KEYS)}")
        if not SLUG.match(str(entry["id"])):
            raise ValidationError(f"{path}: workflow id '{entry['id']}' must be a lowercase slug")
        result.append(
            Workflow(entry["id"], str(entry["description"]).strip(), _existing_file(path, base, entry["file"]))
        )
    return tuple(result)


def load_core(core_dir: Path) -> Core:
    path = core_dir / "core.yaml"
    data = load_yaml(path)
    _check_keys(path, data, CORE_REQUIRED, CORE_OPTIONAL)
    if data["category"] != "core":
        raise ValidationError(f"{path}: category must be 'core'")
    documents = tuple((rel, _existing_file(path, core_dir, rel)) for rel in _str_list(path, data, "documents"))
    return Core(
        version=data["version"],
        description=data["description"].strip(),
        summary=_str_list(path, data, "summary"),
        documents=documents,
        workflows=_workflows(path, data, core_dir),
    )


def load_profile(profile_dir: Path) -> Profile:
    path = profile_dir / "profile.yaml"
    data = load_yaml(path)
    _check_keys(path, data, PROFILE_REQUIRED, PROFILE_OPTIONAL)
    name, category = data["name"], data["category"]
    if name != profile_dir.name:
        raise ValidationError(f"{path}: name '{name}' must match directory '{profile_dir.name}'")
    if category != profile_dir.parent.name:
        raise ValidationError(f"{path}: category '{category}' must match directory '{profile_dir.parent.name}'")
    if not SLUG.match(name):
        raise ValidationError(f"{path}: name '{name}' must be a lowercase slug")
    return Profile(
        id=f"{category}/{name}",
        name=name,
        version=data["version"],
        category=category,
        description=data["description"].strip(),
        summary=_str_list(path, data, "summary"),
        applies_to=_str_list(path, data, "applies_to"),
        workflows=_workflows(path, data, profile_dir),
        requires=_str_list(path, data, "requires"),
        conflicts=_str_list(path, data, "conflicts"),
        guidance=_existing_file(path, profile_dir, "guidance.md"),
    )


def discover_profiles(profiles_dir: Path) -> dict[str, Profile]:
    profiles: dict[str, Profile] = {}
    names: dict[str, str] = {}
    for manifest in sorted(profiles_dir.glob("*/*/profile.yaml")):
        profile = load_profile(manifest.parent)
        if profile.name in names:
            # Generated docs are keyed by name, so names must be unique across categories.
            raise ValidationError(f"profile name '{profile.name}' used by both {names[profile.name]} and {profile.id}")
        names[profile.name] = profile.id
        profiles[profile.id] = profile
    return profiles


def load_preset(path: Path) -> Preset:
    data = load_yaml(path)
    unknown = data.keys() - PRESET_KEYS
    if unknown:
        raise ValidationError(
            f"{path}: presets may only compose profiles; unknown keys: {', '.join(sorted(unknown))}"
        )
    if set(data) != PRESET_KEYS:
        raise ValidationError(f"{path}: presets need exactly {sorted(PRESET_KEYS)}")
    if data["name"] != path.stem:
        raise ValidationError(f"{path}: name '{data['name']}' must match file name '{path.stem}'")
    profiles = _str_list(path, data, "profiles")
    if not profiles:
        raise ValidationError(f"{path}: 'profiles' must not be empty")
    return Preset(data["name"], str(data["description"]).strip(), profiles)


def discover_presets(presets_dir: Path) -> dict[str, Preset]:
    return {p.stem: load_preset(p) for p in sorted(presets_dir.glob("*.yaml"))}


def _normalize(paragraph: str) -> str:
    lines = [re.sub(r"^\s*(#+|[-*]|\d+\.)\s*", "", line) for line in paragraph.splitlines()]
    return re.sub(r"\s+", " ", " ".join(lines)).strip().lower()


def find_duplicate_paragraphs(documents: dict[str, str]) -> list[str]:
    """Return errors for non-trivial paragraphs that appear in more than one place."""
    seen: dict[str, str] = {}
    errors = []
    for label, text in documents.items():
        for paragraph in re.split(r"\n\s*\n", text):
            norm = _normalize(paragraph)
            if len(norm) < MIN_DUPLICATE_PARAGRAPH:
                continue
            if norm in seen:
                errors.append(f"duplicate content in {label} (first seen in {seen[norm]}): {norm[:70]}...")
            else:
                seen[norm] = label
    return errors


def lint_text(label: str, text: str) -> list[str]:
    errors = []
    for match in VENDOR_TERMS.finditer(text):
        errors.append(f"{label}: vendor-specific term '{match.group(0)}' in shared content")
    for match in ABSOLUTE_PATHS.finditer(text):
        errors.append(f"{label}: absolute/machine path '{match.group(0)}' in shared content")
    return errors


def validate_repo(root: Path = REPO_ROOT) -> list[str]:
    """Validate everything under core/, profiles/, presets/. Returns a list of errors."""
    errors: list[str] = []
    try:
        core = load_core(root / "core")
        profiles = discover_profiles(root / "profiles")
        presets = discover_presets(root / "presets")
    except ValidationError as exc:
        return [str(exc)]

    for preset in presets.values():
        for pid in preset.profiles:
            if pid not in profiles:
                errors.append(f"preset '{preset.name}' references unknown profile '{pid}'")
    for profile in profiles.values():
        for ref in profile.requires + profile.conflicts:
            if ref not in profiles:
                errors.append(f"profile '{profile.id}' references unknown profile '{ref}'")

    workflow_ids: dict[str, str] = {}
    for owner, workflows in [("core", core.workflows)] + [(p.id, p.workflows) for p in profiles.values()]:
        for wf in workflows:
            if wf.id in workflow_ids:
                errors.append(f"workflow id '{wf.id}' declared by both {workflow_ids[wf.id]} and {owner}")
            workflow_ids[wf.id] = owner

    shared_files = sorted((root / "core").rglob("*")) + sorted((root / "profiles").rglob("*")) + sorted(
        (root / "presets").rglob("*")
    )
    markdown: dict[str, str] = {}
    for path in shared_files:
        if path.suffix not in {".md", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8")
        label = str(path.relative_to(root))
        errors.extend(lint_text(label, text))
        if path.suffix == ".md":
            markdown[label] = text
    errors.extend(find_duplicate_paragraphs(markdown))
    return errors


def main() -> int:
    errors = validate_repo()
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print("ok: core, profiles, and presets are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
