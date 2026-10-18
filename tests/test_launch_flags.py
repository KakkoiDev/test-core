"""Every place that launches Chromium passes --use-mock-keychain and --password-store=basic (NOTES.md 1).

Without them, on macOS every test browser asks for a keychain; "Reset To Defaults" on that dialog would reset the
person's login keychain."""
import re

from tools_path import ROOT

FLAGS = ("--use-mock-keychain", "--password-store=basic")
SKIP = {"node_modules", ".venv", ".git", ".test-output"}


def source_files():
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in (".py", ".js", ".cjs", ".mjs", ".ts", ".yml", ".yaml") \
                and not SKIP & set(path.relative_to(ROOT).parts) and path.name != "test_launch_flags.py":
            yield path


def test_the_launch_configs_carry_both_flags():
    config = (ROOT / "playwright.config.js").read_text(encoding="utf-8")
    assert all(flag in config for flag in FLAGS) and "launchOptions: { args: CHROMIUM_FLAGS" in config
    conftest = (ROOT / "recipes/python/conftest.py").read_text(encoding="utf-8")
    assert all(flag in conftest for flag in FLAGS) and "def browser_type_launch_args" in conftest


def test_no_other_launch_without_the_flags():
    launch = re.compile(r"\b(?:chromium|browser_type|browserType)\.(?:launch|launch_persistent_context|launchPersistentContext)\(")
    for path in source_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in launch.finditer(text):
            window = text[match.start(): match.start() + 400]
            assert all(flag in window or "CHROMIUM_FLAGS" in window for flag in FLAGS), f"{path}: {window[:120]}"
