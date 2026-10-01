"""Conflicting selections fail loudly instead of silently overriding."""

import pytest

from bootstrap.compose import CompositionError, OutputFile, render_all, resolve_and_compose
from bootstrap.validate import validate_repo

from tests.conftest import write_profile


def test_declared_conflict(repo_copy):
    write_profile(repo_copy, "runtime/alpha", conflicts=["runtime/beta"])
    write_profile(repo_copy, "runtime/beta")
    with pytest.raises(CompositionError, match="declares a conflict"):
        resolve_and_compose("demo", profiles=["runtime/beta", "runtime/alpha"], root=repo_copy)


def test_profile_cannot_replace_core_workflow(repo_copy):
    write_profile(
        repo_copy,
        "runtime/alpha",
        workflows=[{"id": "code-review", "file": "workflows/code-review.md", "description": "mine"}],
    )
    with pytest.raises(CompositionError, match="never replace"):
        resolve_and_compose("demo", profiles=["runtime/alpha"], root=repo_copy)
    assert any("workflow id 'code-review'" in e for e in validate_repo(repo_copy))


def test_duplicate_workflow_between_profiles(repo_copy):
    wf = [{"id": "shared", "file": "workflows/shared.md", "description": "x"}]
    write_profile(repo_copy, "runtime/alpha", workflows=wf)
    write_profile(repo_copy, "runtime/beta", workflows=wf)
    with pytest.raises(CompositionError, match="provided by both"):
        resolve_and_compose("demo", profiles=["runtime/alpha", "runtime/beta"], root=repo_copy)


def test_unknown_requirement(repo_copy):
    write_profile(repo_copy, "runtime/alpha", requires=["runtime/missing"])
    with pytest.raises(CompositionError, match="requires unknown"):
        resolve_and_compose("demo", profiles=["runtime/alpha"], root=repo_copy)


def test_duplicate_content_across_profiles_fails_validation(repo_copy):
    shared = "Always use the shared retry helper for outbound calls so retry behaviour is consistent."
    for pid in ("runtime/alpha", "runtime/beta"):
        pdir = write_profile(repo_copy, pid)
        (pdir / "guidance.md").write_text(f"# {pid}\n\n{shared}\n")
    assert any("duplicate content" in e for e in validate_repo(repo_copy))


def test_vendor_term_in_profile_fails_validation(repo_copy):
    pdir = write_profile(repo_copy, "runtime/alpha")
    (pdir / "guidance.md").write_text("# alpha\n\nCodex should run the tests.\n")
    assert any("vendor-specific" in e for e in validate_repo(repo_copy))


def test_output_path_collision(monkeypatch):
    comp, _ = resolve_and_compose("demo", preset="fastapi-rag")
    from adapters.codex import adapter as codex

    monkeypatch.setattr(codex, "render", lambda c: [OutputFile("CLAUDE.md", "x")])
    with pytest.raises(CompositionError, match="same path"):
        render_all(comp, ["claude", "codex"])


def test_adapter_cannot_write_shared_docs(monkeypatch):
    comp, _ = resolve_and_compose("demo", preset="fastapi-rag")
    from adapters.codex import adapter as codex

    monkeypatch.setattr(codex, "render", lambda c: [OutputFile("docs/engineering/README.md", "x")])
    with pytest.raises(CompositionError, match="may not write shared docs"):
        render_all(comp, ["codex"])
