"""Documentation cross-links resolve, so the docs can link instead of repeating each other."""

import re

import pytest

from bootstrap.validate import REPO_ROOT

DOCS = [REPO_ROOT / "README.md", *sorted((REPO_ROOT / "docs").rglob("*.md"))]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def relative_links(path):
    # Skip code blocks and HTML comments (the ADR template has placeholder links in one).
    text = re.sub(r"```.*?```|<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    for target in LINK.findall(text):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
            continue  # external URL or same-page anchor
        yield target.split("#", 1)[0]


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_relative_links_resolve(doc):
    broken = [t for t in relative_links(doc) if not (doc.parent / t).exists()]
    assert not broken, f"broken links in {doc.name}: {broken}"


def test_every_adr_is_indexed():
    decisions = REPO_ROOT / "docs" / "decisions"
    index = (decisions / "README.md").read_text(encoding="utf-8")
    for adr in sorted(decisions.glob("adr-[0-9]*.md")):
        if adr.name != "adr-0000-template.md":
            assert adr.name in index, f"{adr.name} missing from decisions/README.md"
