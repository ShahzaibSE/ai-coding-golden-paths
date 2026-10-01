"""The shared Git/testing/review workflows: present, neutral, safe, and exposed as Claude skills."""

import re

import pytest

from bootstrap.compose import REPO_ROOT, load_adapter, resolve_and_compose
from bootstrap.init import run
from bootstrap.validate import ABSOLUTE_PATHS, VENDOR_TERMS

from tests.conftest import tree

GOLDEN = ["git-review", "git-commit", "git-release", "run-tests", "code-review"]
EXPLICIT_ONLY = {"git-commit", "git-release"}
WORKFLOWS = REPO_ROOT / "core" / "workflows"


@pytest.fixture(scope="module")
def skills():
    comp, _ = resolve_and_compose("demo", preset="fastapi-rag")
    return {f.path: f.content for f in load_adapter("claude").render(comp) if f.path.startswith(".claude/skills/")}


def frontmatter_text(text):
    return re.match(r"^---\n(.*?)\n---\n", text, re.S).group(1)


@pytest.mark.parametrize("wf", GOLDEN)
def test_skill_exists_with_slash_command_name(skills, wf):
    text = skills[f".claude/skills/{wf}/SKILL.md"]
    meta = frontmatter_text(text)
    assert re.search(rf"^name: {wf}$", meta, re.M)
    assert re.match(r"^[a-z0-9-]{1,64}$", wf)  # the skill name is the /command
    assert re.search(r'^description: ".{20,}"$', meta, re.M)
    assert f"docs/engineering/workflows/{wf}.md" in text  # thin wrapper, not an inlined copy


@pytest.mark.parametrize("wf", GOLDEN)
def test_only_mutating_git_skills_require_explicit_invocation(skills, wf):
    meta = frontmatter_text(skills[f".claude/skills/{wf}/SKILL.md"])
    assert ("disable-model-invocation: true" in meta) == (wf in EXPLICIT_ONLY)


@pytest.mark.parametrize("wf", GOLDEN)
def test_canonical_workflow_is_tool_neutral(wf):
    text = (WORKFLOWS / f"{wf}.md").read_text()
    assert not VENDOR_TERMS.search(text)
    assert not ABSOLUTE_PATHS.search(text)
    assert "disable-model-invocation" not in text


def test_git_release_keeps_its_safety_rules():
    text = (WORKFLOWS / "git-release.md").read_text().lower()
    for required in ("never force-push", "reset --hard", "git clean", "rebase", "overwrite remote history", "ambiguous"):
        assert required in text, required


def test_git_commit_never_pushes_and_git_review_never_mutates():
    commit = (WORKFLOWS / "git-commit.md").read_text()
    assert "never pushes" in commit and "git add ." in commit
    review = (WORKFLOWS / "git-review.md").read_text()
    assert "read-only" in review
    assert not re.search(r"^\d+\. .*\bgit (add|commit|push)\b", review, re.M)


def test_rerun_does_not_duplicate_or_overwrite_skills(tmp_path):
    target = tmp_path / "app"
    run(target, ["claude"], preset="fastapi-rag")
    before = {p for p in tree(target) if p.startswith(".claude/skills/")}
    edited = target / ".claude/skills/git-release/SKILL.md"
    edited.write_text(edited.read_text() + "\nlocal note\n")
    run(target, ["claude"])
    after = {p for p in tree(target) if p.startswith(".claude/skills/")}
    assert before == after
    assert "local note" in edited.read_text()
