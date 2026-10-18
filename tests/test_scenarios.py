"""tools/scenarios.py: parse Given/When/Then, write a skeleton per language, check every scenario has its test."""
import textwrap

from tools_path import ROOT
import scenarios

TASK = ROOT / "recipes/shared/task-example.md"


def test_parses_the_example_task():
    parsed = scenarios.parse(TASK.read_text(encoding="utf-8"))

    assert [s.title for s in parsed] == ["Add a task", "Delete a task", "An empty title is not added"]
    assert parsed[0].given == ["I am signed in with an empty list"]
    assert parsed[0].then == ['I see "Buy milk" in the list', 'the count says "1 task"']


def test_parses_a_gherkin_block():
    text = textwrap.dedent("""
        ```gherkin
        Scenario: Sign in
          Given I am on the sign-in page
          When I sign in
          Then I see my tasks
          But I do not see the sign-in form
        ```
    """)
    [s] = scenarios.parse(text)
    assert (s.title, s.when, s.then) == ("Sign in", ["I sign in"], ["I see my tasks", "I do not see the sign-in form"])


def test_python_names_keep_japanese():
    assert scenarios.python_name("Add a task") == "test_add_a_task"
    assert scenarios.python_name("タスクを追加する") == "test_タスクを追加する"


def test_the_skeletons_compile_and_name_each_scenario(tmp_path):
    parsed = scenarios.parse(TASK.read_text(encoding="utf-8"))
    python = scenarios.skeleton(parsed, "python", "task.md")
    compile(python, "skeleton.py", "exec")
    assert '@pytest.mark.scenario("Add a task")' in python and "def test_add_a_task(" in python
    js = scenarios.skeleton(parsed, "js", "task.md")
    assert 'test("Delete a task", async' in js and "// When I delete" in js


def test_both_recipes_implement_every_scenario():
    for test_file in ["recipes/python/scenario-e2e/test_task_scenarios.py", "recipes/js/scenario-e2e/task-scenarios.spec.js"]:
        rows, ok = scenarios.check(TASK, [ROOT / test_file], [])
        assert ok, rows


def test_a_missing_test_fails(tmp_path):
    test_file = tmp_path / "test_partial.py"
    test_file.write_text('@pytest.mark.scenario("Add a task")\ndef test_x(page): ...\n'
                         'def test_delete_a_task(page): ...\n', encoding="utf-8")

    rows, ok = scenarios.check(TASK, [test_file], [])

    assert not ok
    assert [r["status"] for r in rows] == ["has a test", "has a test", "no test"]


def test_junit_requires_each_test_to_have_run_and_passed(tmp_path):
    spec = tmp_path / "task.spec.js"
    spec.write_text("test('Add a task', () => {});\ntest('Delete a task', () => {});\n"
                    "test(\"An empty title is not added\", () => {});\n", encoding="utf-8")
    report = tmp_path / "junit.xml"
    report.write_text('<testsuites><testsuite><testcase name="Add a task"/>'
                      '<testcase name="Delete a task"><failure message="boom"/></testcase></testsuite></testsuites>')

    rows, ok = scenarios.check(TASK, [spec], [report])

    assert not ok
    assert [r["status"] for r in rows] == ["passed", "failed", "did not run"]


def test_pytest_junit_names_with_browser_suffix_count(tmp_path):
    test_file = ROOT / "recipes/python/scenario-e2e/test_task_scenarios.py"
    report = tmp_path / "junit.xml"
    report.write_text('<testsuites><testsuite>' + "".join(
        f'<testcase name="{n}[chromium]"/>' for n in
        ["test_add_a_task", "test_delete_a_task", "test_an_empty_title_is_not_added"]) + '</testsuite></testsuites>')

    rows, ok = scenarios.check(TASK, [test_file], [report])

    assert ok, rows


def test_a_task_without_scenarios_fails(tmp_path):
    task = tmp_path / "task.md"
    task.write_text("# Task\nNo scenarios yet.\n", encoding="utf-8")
    assert scenarios.main(["check", str(task), "--tests", str(TASK)]) == 1
