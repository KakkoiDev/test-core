"""functional/runner.py: a scenario runs step by step at a level; unknown steps fail before anything runs."""
import pytest

from functional import Registry, StepFailed, UnknownStep, load_scenarios, parse_scenarios, run_scenario, scenario_tests

TASK = """## Scenarios

### US-7 Add two tasks
Given an empty list
When I add the task "Buy milk"
And I add the task "牛乳"
Then the list has 2 tasks
"""


def registry(log: list) -> Registry:
    steps = Registry()
    steps.step("Given an empty list", level="unit")(lambda world: (log.append("given"), setattr(world, "tasks", [])))
    steps.step("When I add the task {title}", level="unit")(lambda world, title: (log.append(title), world.tasks.append(title)))

    @steps.step("Then the list has {n} tasks", level="unit")
    def count(world, n):
        log.append(n)
        assert len(world.tasks) == n, f"{len(world.tasks)} tasks"
    return steps


def test_a_scenario_runs_its_steps_in_order_and_returns_the_world():
    log = []
    [scenario] = parse_scenarios(TASK)
    world = run_scenario(scenario, level="unit", registry=registry(log), world={"extra": 1})
    assert log == ["given", "Buy milk", "牛乳", 2]
    assert (world.level, world.scenario, world.extra, world.tasks) == ("unit", "US-7 Add two tasks", 1, ["Buy milk", "牛乳"])


def test_an_unknown_step_fails_before_the_first_step_runs():
    log = []
    [scenario] = parse_scenarios(TASK.replace('And I add the task "牛乳"', 'And I add task "牛乳"'), source="t.md")
    with pytest.raises(UnknownStep) as error:
        run_scenario(scenario, level="unit", registry=registry(log))
    assert log == []
    assert 't.md:6: scenario "US-7 Add two tasks"' in str(error.value)
    assert "When I add the task {title}" in str(error.value)


def test_a_failing_step_says_which_scenario_and_step():
    [scenario] = parse_scenarios(TASK.replace("2 tasks", "3 tasks"), source="t.md")
    with pytest.raises(StepFailed, match=r't.md:7: scenario "US-7 Add two tasks", step "Then the list has 3 tasks" failed: 2 tasks'):
        run_scenario(scenario, level="unit", registry=registry([]))


def test_a_step_missing_at_the_level_fails_before_running():
    [scenario] = parse_scenarios(TASK)
    with pytest.raises(LookupError, match="no e2e implementation"):
        run_scenario(scenario, level="e2e", registry=registry([]))


def test_load_scenarios_needs_scenarios(tmp_path):
    (tmp_path / "t.md").write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no scenarios"):
        load_scenarios(tmp_path / "t.md")


def test_scenario_tests_makes_one_pytest_test_per_scenario_named_after_its_heading(tmp_path):
    task = tmp_path / "task.md"
    task.write_text(TASK + "\n### Scenario: Old form\nGiven an empty list\nThen the list has 0 tasks\n", encoding="utf-8")
    seen = []

    def world(tmp_path, request):
        seen.append(request.node.name if hasattr(request, "node") else request)
        return {"folder": tmp_path}

    tests = scenario_tests(task, level="unit", registry=registry([]), world=world)
    assert list(tests) == ["test_us_7_add_two_tasks", "test_old_form"]
    test = tests["test_us_7_add_two_tasks"]
    assert [m.args for m in test.pytestmark] == [("US-7 Add two tasks",)]
    import inspect
    assert list(inspect.signature(test).parameters) == ["tmp_path", "request"]
    test(tmp_path=tmp_path, request="r")
    assert seen == ["r"]


def test_scenario_tests_refuses_an_unknown_step_at_collection(tmp_path):
    task = tmp_path / "task.md"
    task.write_text(TASK.replace("Then the list has 2 tasks", "Then I see two tasks"), encoding="utf-8")
    with pytest.raises(UnknownStep, match="Then the list has {n} tasks"):
        scenario_tests(task, level="unit", registry=registry([]))
