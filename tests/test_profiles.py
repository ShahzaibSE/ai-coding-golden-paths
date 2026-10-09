"""Profiles are valid, independently composable, and do not duplicate each other or core."""

import itertools

import pytest

from bootstrap.compose import CompositionError, compose, render_all, resolve_and_compose
from bootstrap.validate import REPO_ROOT, ValidationError, discover_profiles, find_duplicate_paragraphs, load_profile

from tests.conftest import write_profile

PROFILES = discover_profiles(REPO_ROOT / "profiles")


def with_requirements(ids):
    resolved = []
    for pid in ids:
        for dep in PROFILES[pid].requires:
            if dep not in resolved:
                resolved.append(dep)
        if pid not in resolved:
            resolved.append(pid)
    return resolved


def test_initial_profiles_present():
    assert set(PROFILES) == {
        "runtime/python-backend",
        "runtime/fastapi",
        "runtime/nextjs",
        "runtime/react-vite",
        "ai/rag",
        "ai/agentic-ai",
    }


@pytest.mark.parametrize("pid", sorted(PROFILES))
def test_each_profile_composes_alone(pid):
    comp = compose("demo", with_requirements([pid]))
    paths = {f.path for f in render_all(comp, ["claude", "codex"])}
    assert f"docs/engineering/profiles/{PROFILES[pid].name}.md" in paths


def declared_conflict(pair):
    a, b = pair
    return b in PROFILES[a].conflicts or a in PROFILES[b].conflicts


ALL_PAIRS = list(itertools.combinations(sorted(PROFILES), 2))
COMPATIBLE_PAIRS = [pair for pair in ALL_PAIRS if not declared_conflict(pair)]
CONFLICTING_PAIRS = [pair for pair in ALL_PAIRS if declared_conflict(pair)]


@pytest.mark.parametrize("pair", COMPATIBLE_PAIRS)
def test_every_compatible_profile_pair_composes(pair):
    comp = compose("demo", with_requirements(list(pair)))
    assert {p.id for p in comp.profiles} >= set(pair)


def test_only_intended_pairs_are_excluded_as_conflicting():
    # Excluding a pair from composition must be a deliberate, reviewed decision.
    assert {frozenset(pair) for pair in CONFLICTING_PAIRS} == {frozenset({"runtime/nextjs", "runtime/react-vite"})}


@pytest.mark.parametrize("pair", CONFLICTING_PAIRS)
@pytest.mark.parametrize("reverse", [False, True], ids=["declared-order", "reversed-order"])
def test_conflicting_profile_pairs_are_rejected_in_both_orders(pair, reverse):
    selection = list(reversed(pair)) if reverse else list(pair)
    with pytest.raises(CompositionError, match="declares a conflict"):
        resolve_and_compose("demo", profiles=selection)


def test_duplicate_paragraph_detection():
    text = "Every outbound network call has an explicit timeout and a bounded retry policy."
    assert find_duplicate_paragraphs({"core/a.md": text, "profiles/b.md": text})
    assert find_duplicate_paragraphs({"core/a.md": text, "profiles/b.md": "Something else entirely."}) == []


def test_invalid_profile_rejected(tmp_path):
    pdir = write_profile(tmp_path, "runtime/broken", version="one")
    with pytest.raises(ValidationError, match="semver"):
        load_profile(pdir)


def test_unknown_profile_key_rejected(tmp_path):
    pdir = write_profile(tmp_path, "runtime/extra", overrides=["core"])
    with pytest.raises(ValidationError, match="unknown keys"):
        load_profile(pdir)


def test_name_must_match_directory(tmp_path):
    pdir = write_profile(tmp_path, "runtime/right", name="wrong")
    with pytest.raises(ValidationError, match="must match directory"):
        load_profile(pdir)
