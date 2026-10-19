"""adopt/adopt.py: one command puts test-core in another repository, pinned and verifiable, and the copy works there."""
import json
import os
import subprocess
import sys

import pytest

from tools_path import ROOT

sys.path.insert(0, str(ROOT / "adopt"))
import adopt  # noqa: E402


@pytest.fixture
def target(tmp_path):
    repo = tmp_path / "other-core"
    repo.mkdir()
    adopt.adopt(repo)
    return repo


def run(*args, cwd, env=None):
    return subprocess.run([*args], cwd=cwd, capture_output=True, text=True, env={**os.environ, **(env or {})})


def test_it_copies_the_tools_the_library_the_blocks_and_the_project_files(target):
    base = target / "test-core"
    for path in ["tools/vocab.py", "tools/scenarios.py", "tools/e2e_coverage.py", "tools/flaky_lint.py",
                 "tools/blocks_from_app_blocks.py", "functional/__init__.py", "functional/js/index.js",
                 "functional/blocks/python/log_in.py", "functional/blocks/js/LogIn.js", "functional/blocks/vocabulary.json",
                 "functional/blocks/spec.json", "package.json", "MANIFEST.json", "adopt.py", "README.md",
                 "vocabulary.json", "scenarios-template.md"]:
        assert (base / path).is_file(), path
    assert (target / ".github/workflows/test-core.yml").is_file()
    manifest = json.loads((base / "MANIFEST.json").read_text())
    assert manifest["test-core"] == "https://github.com/KakkoiDev/test-core" and manifest["commit"]
    assert "functional/primitives.py" in manifest["files"] and "README.md" not in manifest["files"]
    assert not any("__pycache__" in p for p in manifest["files"])


def test_the_copy_works_in_the_other_repository(target):
    tools = target / "test-core" / "tools"
    vocab = run(sys.executable, str(tools / "vocab.py"), "check", "test-core/scenarios-template.md", "--vocab",
                "test-core/vocabulary.json", "test-core/functional/blocks/vocabulary.json", cwd=target)
    assert vocab.returncode == 0, vocab.stdout
    py = run(sys.executable, "-c", "from functional.blocks.python import BLOCKS; from functional import Registry; print(len(BLOCKS))",
             cwd=target, env={"PYTHONPATH": "test-core"})
    assert py.stdout.strip() == "8", py.stderr
    js = run("node", "-e", "import('./test-core/functional/blocks/js/index.js').then((m) => console.log(Object.keys(m.BLOCKS).length))",
             cwd=target)
    assert js.stdout.strip() == "8", js.stderr
    check = run(sys.executable, str(tools / "blocks_from_app_blocks.py"), "--kit", str(ROOT / "tests/fixtures/app-blocks"),
                "--check", cwd=target)
    assert check.returncode == 0, check.stdout


def test_verify_catches_an_edit_in_place(target):
    base = target / "test-core"
    assert adopt.verify(base) == []
    (base / "functional/primitives.py").write_text("# edited\n", encoding="utf-8")
    (base / "tools/vocab.py").unlink()
    assert adopt.verify(base) == ["edited in place: test-core/functional/primitives.py (change test-core, then adopt.py --update)",
                                  "missing: test-core/tools/vocab.py"]
    result = run(sys.executable, str(base / "adopt.py"), "--verify", str(base), cwd=target)
    assert result.returncode == 1


def test_a_second_run_refuses_changes_without_update_and_keeps_the_projects_files(target):
    base = target / "test-core"
    assert all(line.startswith("keep ") for line in adopt.adopt(target))  # same version: nothing to do
    (base / "vocabulary.json").write_text('{"steps": [{"step": "Given mine"}]}\n', encoding="utf-8")
    (base / "functional/primitives.py").write_text("# old\n", encoding="utf-8")
    manifest = json.loads((base / "MANIFEST.json").read_text())
    manifest["files"]["functional/gone.py"] = "0"
    (base / "MANIFEST.json").write_text(json.dumps(manifest))
    (base / "functional/gone.py").write_text("# from an older test-core\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="functional/primitives.py"):
        adopt.adopt(target)
    done = adopt.adopt(target, update=True)
    assert "update test-core/functional/primitives.py" in done and "remove test-core/functional/gone.py" in done
    assert "keep test-core/vocabulary.json (the project's)" in done
    assert "Given mine" in (base / "vocabulary.json").read_text()
    assert adopt.verify(base) == []


def test_dry_run_and_no_workflow(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    done = adopt.adopt(repo, dry_run=True, workflow=False)
    assert "add test-core/tools/vocab.py" in done and not any("workflow" in d for d in done)
    assert list(repo.iterdir()) == []


def test_the_workflow_uses_only_copied_tools():
    workflow = (ROOT / "adopt/templates/test-core.yml").read_text(encoding="utf-8")
    for tool in ["adopt.py --verify", "tools/flaky_lint.py", "tools/vocab.py check", "tools/scenarios.py check", "tools/e2e_coverage.py"]:
        assert f"test-core/{tool}" in workflow
