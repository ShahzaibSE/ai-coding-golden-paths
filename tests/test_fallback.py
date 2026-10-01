"""The fallback property: switching between coding agents never redefines the engineering knowledge.

Only the instruction mechanism (CLAUDE.md + .claude/ vs AGENTS.md, ...) may differ.
Every adapter in adapters/ is covered automatically.
"""

import itertools
import re

import pytest

from bootstrap.compose import available_adapters, resolve_and_compose
from bootstrap.init import MANIFEST, run

from tests.conftest import tree

PRESETS = ["fastapi-rag", "fullstack-agentic-ai"]
TOOLS = available_adapters()


def shared_docs(target):
    return {p: b for p, b in tree(target).items() if p.startswith("docs/engineering/")}


def entry_text(target):
    """Everything a tool reads besides the shared docs: its own instruction files."""
    return "\n".join(
        b.decode() for p, b in tree(target).items() if not p.startswith("docs/engineering/") and p != MANIFEST
    )


def referenced_docs(text):
    return set(re.findall(r"docs/engineering/[\w./-]+\.md", text))


def test_at_least_two_adapters():
    assert {"claude", "codex"} <= set(TOOLS)


@pytest.mark.parametrize("preset", PRESETS)
def test_shared_knowledge_is_identical_for_every_tool_choice(tmp_path, preset):
    selections = [[t] for t in TOOLS] + [TOOLS]
    trees = []
    for i, tools in enumerate(selections):
        target = tmp_path / str(i) / "app"
        run(target, tools, preset=preset)
        trees.append(shared_docs(target))
    assert trees[0]
    assert all(t == trees[0] for t in trees)


@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize("preset", PRESETS)
def test_each_tool_reaches_all_shared_knowledge(tmp_path, preset, tool):
    target = tmp_path / "app"
    run(target, [tool], preset=preset)
    comp, _ = resolve_and_compose("app", preset=preset)
    text = entry_text(target)

    missing = (set(comp.doc_paths) | {"docs/engineering/PROJECT.md"}) - referenced_docs(text)
    assert not missing, f"{tool} cannot reach {sorted(missing)}"
    for bullet in comp.core_summary + tuple(b for p in comp.profiles for b in p.summary):
        assert bullet in text, f"{tool} is missing contract line: {bullet}"
    for wf in comp.workflows:
        assert wf.description in text, f"{tool} does not expose workflow {wf.id}"


@pytest.mark.parametrize("first,second", list(itertools.permutations(TOOLS, 2)))
def test_adding_a_tool_later_equals_generating_both(tmp_path, first, second):
    together = tmp_path / "together" / "app"
    run(together, [first, second], preset="fullstack-agentic-ai")

    sequential = tmp_path / "sequential" / "app"
    run(sequential, [first], preset="fullstack-agentic-ai")
    run(sequential, [second])  # selection comes from the recorded manifest, not re-specified
    assert tree(together) == tree(sequential)


def test_switching_tools_only_adds_entry_points(tmp_path):
    target = tmp_path / "app"
    run(target, ["claude"], preset="fastapi-rag")
    result = run(target, ["codex"])
    created = {a.file.path for a in result.actions if a.kind == "create"}
    assert created == {"AGENTS.md"}


def test_explicit_profiles_match_equivalent_preset(tmp_path):
    a, b = tmp_path / "a" / "app", tmp_path / "b" / "app"
    run(a, TOOLS, preset="fastapi-rag")
    run(b, TOOLS, profiles=["runtime/python-backend", "runtime/fastapi", "ai/rag"])
    assert shared_docs(a) == shared_docs(b)
    assert entry_text(a) == entry_text(b)
