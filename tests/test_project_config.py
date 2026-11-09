import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_every_pytest_testpath_exists():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    paths = config["tool"]["pytest"]["ini_options"]["testpaths"]

    missing = [path for path in paths if not (ROOT / path).is_dir()]

    assert missing == []
