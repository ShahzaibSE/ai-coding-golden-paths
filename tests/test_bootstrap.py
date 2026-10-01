"""Bootstrap safety: dry-run, idempotency, and protection of existing files."""

import pytest

from bootstrap import init
from bootstrap.init import CONFLICT, CREATE, KEEP, UNCHANGED, UPDATE, InitError, run

from tests.conftest import tree


def kinds(result):
    return {a.file.path: a.kind for a in result.actions}


def test_dry_run_writes_nothing(tmp_path):
    target = tmp_path / "app"
    result = run(target, ["claude", "codex"], preset="fastapi-rag", dry_run=True)
    assert not target.exists()
    assert set(kinds(result).values()) == {CREATE}

    target.mkdir()
    (target / "README.md").write_text("existing")
    before = tree(target)
    run(target, ["claude"], preset="fastapi-rag", dry_run=True)
    assert tree(target) == before


def test_rerun_is_idempotent(tmp_path):
    target = tmp_path / "app"
    run(target, ["claude", "codex"], preset="fastapi-rag")
    first = tree(target)
    result = run(target, ["claude", "codex"], preset="fastapi-rag")
    assert tree(target) == first
    assert set(kinds(result).values()) == {UNCHANGED, KEEP}
    assert kinds(result)["docs/engineering/PROJECT.md"] == KEEP


def test_existing_unmanaged_file_aborts_without_writing(tmp_path, capsys):
    target = tmp_path / "app"
    target.mkdir()
    (target / "CLAUDE.md").write_text("my own instructions\n")
    before = tree(target)

    result = run(target, ["claude"], preset="fastapi-rag")
    assert kinds(result)["CLAUDE.md"] == CONFLICT
    assert not result.written
    assert tree(target) == before

    exit_code = init.main(["--target", str(target), "--tool", "claude", "--preset", "fastapi-rag"])
    assert exit_code == 2
    assert "not managed" in capsys.readouterr().out
    assert tree(target) == before


def test_edited_generated_file_is_kept(tmp_path):
    target = tmp_path / "app"
    run(target, ["claude"], preset="fastapi-rag")
    edited = (target / "CLAUDE.md").read_text() + "\n- Team-specific note.\n"
    (target / "CLAUDE.md").write_text(edited)

    result = run(target, ["claude"])
    assert kinds(result)["CLAUDE.md"] == KEEP
    assert (target / "CLAUDE.md").read_text() == edited
    # And it stays protected on later runs.
    assert kinds(run(target, ["claude"]))["CLAUDE.md"] == KEEP


def test_project_seed_survives_edits(tmp_path):
    target = tmp_path / "app"
    run(target, ["codex"], preset="fastapi-rag")
    project = target / "docs/engineering/PROJECT.md"
    project.write_text("# Our architecture\n")
    run(target, ["codex", "claude"])
    assert project.read_text() == "# Our architecture\n"


def test_unmodified_generated_file_is_updated(tmp_path, monkeypatch):
    target = tmp_path / "app"
    run(target, ["codex"], preset="fastapi-rag")
    from adapters.codex import adapter as codex

    original = codex.render
    monkeypatch.setattr(codex, "render", lambda c: [type(f)(f.path, f.content + "\nnew line\n") for f in original(c)])
    result = run(target, ["codex"])
    assert kinds(result)["AGENTS.md"] == UPDATE
    assert (target / "AGENTS.md").read_text().endswith("new line\n")


def test_changing_profiles_is_refused(tmp_path):
    target = tmp_path / "app"
    run(target, ["claude"], preset="fastapi-rag")
    with pytest.raises(InitError, match="differs from the recorded"):
        run(target, ["claude"], preset="fullstack-agentic-ai")


def test_input_errors(tmp_path):
    with pytest.raises(InitError, match="unknown tool"):
        run(tmp_path / "a", ["copilot"], preset="fastapi-rag")
    with pytest.raises(InitError, match="no profiles selected"):
        run(tmp_path / "a", ["claude"])
    with pytest.raises(InitError, match="at least one --tool"):
        run(tmp_path / "a", [], preset="fastapi-rag")
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / ".golden-paths.yaml").write_text("something: else\n")
    with pytest.raises(InitError, match="not written by"):
        run(tmp_path / "b", ["claude"], preset="fastapi-rag")


def test_symlink_escape_is_refused(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    target = tmp_path / "app"
    target.mkdir()
    (target / ".claude").symlink_to(outside, target_is_directory=True)
    with pytest.raises(InitError, match="escapes the target"):
        run(target, ["claude"], preset="fastapi-rag")
    assert list(outside.iterdir()) == []


def test_project_name_comes_from_target_or_flag(tmp_path):
    run(tmp_path / "billing-service", ["codex"], preset="fastapi-rag")
    assert (tmp_path / "billing-service/AGENTS.md").read_text().splitlines()[1] == "# billing-service"
    run(tmp_path / "x", ["codex"], preset="fastapi-rag", project_name="Billing")
    assert "# Billing" in (tmp_path / "x/AGENTS.md").read_text()
