"""The committed example matches what the generator produces today.

Regenerate after intentional changes:
    rm -rf examples/fastapi-rag && python bootstrap/init.py --target examples/fastapi-rag \
        --tool claude --tool codex --preset fastapi-rag
"""

from bootstrap.init import run
from bootstrap.validate import REPO_ROOT

from tests.conftest import tree


def test_example_matches_generator(tmp_path):
    target = tmp_path / "fastapi-rag"
    run(target, ["claude", "codex"], preset="fastapi-rag")
    assert tree(target) == tree(REPO_ROOT / "examples" / "fastapi-rag")
