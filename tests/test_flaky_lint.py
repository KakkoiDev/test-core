"""tools/flaky_lint.py finds fixed waits, focused tests, network-idle waits and real hosts; the recipes are clean."""
from tools_path import ROOT
import flaky_lint


def lint_text(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return [message for _, message, _ in flaky_lint.lint(path)]


def test_finds_each_flaky_pattern(tmp_path):
    found = lint_text(tmp_path, "test_x.py", "time.sleep(1)\npage.wait_for_timeout(500)\n"
                      'page.goto("https://example.com")\npage.wait_for_load_state("networkidle")\n')
    assert len(found) == 4
    found = lint_text(tmp_path, "x.spec.js", "await page.waitForTimeout(500);\ntest.only('x', () => {});\n"
                      "await new Promise((r) => setTimeout(r, 100));\n")
    assert len(found) == 3


def test_local_hosts_and_allowed_lines_pass(tmp_path):
    assert lint_text(tmp_path, "test_ok.py", 'page.goto("http://127.0.0.1:8000")\n'
                     "time.sleep(0.1)  # flaky-lint: allow the device needs a settle time, see issue 4\n") == []


def test_the_recipes_have_no_flaky_patterns():
    assert flaky_lint.main([str(ROOT / "recipes"), str(ROOT / "sample_app")]) == 0
