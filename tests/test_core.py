"""Core smoke tests: the shared core loads, is complete, and stays vendor-neutral."""

from bootstrap.validate import REPO_ROOT, lint_text, load_core, validate_repo


def test_repository_validates():
    assert validate_repo() == []


def test_core_loads_with_documents_and_workflows():
    core = load_core(REPO_ROOT / "core")
    assert {rel for rel, _ in core.documents} == {
        "standards/engineering.md",
        "standards/testing.md",
        "standards/security.md",
        "standards/git-workflow.md",
        "governance/privacy-baseline.md",
    }
    assert [wf.id for wf in core.workflows] == ["implementation", "code-review"]
    assert core.summary, "core must provide an operating-contract summary"


def test_every_core_markdown_file_is_declared():
    core = load_core(REPO_ROOT / "core")
    declared = {src for _, src in core.documents} | {wf.source for wf in core.workflows}
    on_disk = {p.resolve() for p in (REPO_ROOT / "core").rglob("*.md")}
    assert on_disk == declared


def test_lint_flags_vendor_terms_and_machine_paths():
    assert lint_text("x", "Claude should do this")
    assert lint_text("x", "see AGENTS.md")
    assert lint_text("x", "stored in /Users/someone/dev")
    assert lint_text("x", "Validate input at the boundary.") == []
