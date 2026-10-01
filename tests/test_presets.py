"""Presets are pure composition and resolve deterministically."""

import pytest

from bootstrap.compose import CompositionError, resolve_and_compose
from bootstrap.validate import REPO_ROOT, ValidationError, discover_presets, load_preset


def ids(**kwargs):
    comp, notes = resolve_and_compose("demo", **kwargs)
    return [p.id for p in comp.profiles], notes


def test_fastapi_rag_resolution():
    assert ids(preset="fastapi-rag")[0] == ["runtime/python-backend", "runtime/fastapi", "ai/rag"]


def test_fullstack_agentic_ai_resolution():
    assert ids(preset="fullstack-agentic-ai")[0] == ["runtime/python-backend", "runtime/nextjs", "ai/agentic-ai"]


def test_presets_contain_only_composition_keys():
    for preset in discover_presets(REPO_ROOT / "presets").values():
        assert preset.profiles


def test_preset_with_content_is_rejected(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("name: bad\ndescription: x\nprofiles: [ai/rag]\ninstructions: do things\n")
    with pytest.raises(ValidationError, match="only compose"):
        load_preset(path)


def test_requires_are_auto_inserted_before_dependents():
    resolved, notes = ids(profiles=["runtime/fastapi"])
    assert resolved == ["runtime/python-backend", "runtime/fastapi"]
    assert any("required by" in n for n in notes)


def test_preset_plus_explicit_profiles_dedupes():
    resolved, notes = ids(preset="fastapi-rag", profiles=["ai/rag", "runtime/nextjs"])
    assert resolved == ["runtime/python-backend", "runtime/fastapi", "ai/rag", "runtime/nextjs"]
    assert any("more than once" in n for n in notes)


def test_unknown_preset_and_profile():
    with pytest.raises(CompositionError, match="unknown preset"):
        ids(preset="nope")
    with pytest.raises(CompositionError, match="unknown profile"):
        ids(profiles=["ai/nope"])
