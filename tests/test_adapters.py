"""Adapter output is native, concise, deterministic, and points into the shared docs."""

import re

import pytest
import yaml

from bootstrap.compose import load_adapter, render_all, resolve_and_compose


@pytest.fixture(scope="module")
def comp():
    return resolve_and_compose("demo", preset="fullstack-agentic-ai")[0]


def by_path(files):
    return {f.path: f.content for f in files}


def frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, "missing YAML frontmatter"
    return yaml.safe_load(match.group(1))


def test_claude_outputs(comp):
    files = by_path(load_adapter("claude").render(comp))
    assert "CLAUDE.md" in files
    assert "@docs/engineering/PROJECT.md" in files["CLAUDE.md"]
    assert len(files["CLAUDE.md"].splitlines()) <= 80

    # One scoped rule per profile with file globs; agentic-ai has none.
    assert set(p for p in files if p.startswith(".claude/rules/")) == {
        ".claude/rules/python-backend.md",
        ".claude/rules/nextjs.md",
    }
    rule = files[".claude/rules/nextjs.md"]
    assert frontmatter(rule)["paths"] == ["**/*.ts", "**/*.tsx", "app/**", "next.config.*"]
    # Imports resolve relative to the rule file.
    assert "@../../docs/engineering/profiles/nextjs.md" in rule

    for wf in comp.workflows:
        meta = frontmatter(files[f".claude/skills/{wf.id}/SKILL.md"])
        assert meta == {"name": wf.id, "description": wf.description}

    agent = frontmatter(files[".claude/agents/code-reviewer.md"])
    assert agent["name"] == "code-reviewer" and "Edit" not in agent["tools"]


def test_claude_entry_does_not_embed_core(comp):
    claude_md = by_path(load_adapter("claude").render(comp))["CLAUDE.md"]
    for doc in comp.core_docs:
        body = doc.source.read_text().split("\n", 2)[2][:200]
        assert body not in claude_md


def test_codex_outputs(comp):
    files = by_path(load_adapter("codex").render(comp))
    assert set(files) == {"AGENTS.md"}
    assert len(files["AGENTS.md"].splitlines()) <= 100
    assert "docs/engineering/PROJECT.md" in files["AGENTS.md"]


def test_no_unrendered_placeholders(comp):
    for f in render_all(comp, ["claude", "codex"]):
        assert not re.search(r"\$[a-z_]+", f.content), f.path


@pytest.mark.parametrize("tool", ["claude", "codex"])
def test_rendering_is_deterministic(tool):
    first = by_path(render_all(resolve_and_compose("demo", preset="fastapi-rag")[0], [tool]))
    second = by_path(render_all(resolve_and_compose("demo", preset="fastapi-rag")[0], [tool]))
    assert first == second


def test_adapters_contain_no_absolute_paths(comp):
    for f in render_all(comp, ["claude", "codex"]):
        assert not re.search(r"(/Users/|/home/|[A-Za-z]:\\)", f.content), f.path
