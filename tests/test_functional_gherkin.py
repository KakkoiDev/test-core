"""functional/gherkin.py: reading scenarios (with or without a story id), matching steps, the nearest known step.

The same cases are checked in JavaScript (tests/js/functional.test.js) from tests/fixtures/gherkin-cases.json."""
import json
from pathlib import Path

import pytest

from functional.gherkin import compile_pattern, match_pattern, nearest, parse_scenarios, shape, similarity

CASES = json.loads((Path(__file__).parent / "fixtures" / "gherkin-cases.json").read_text(encoding="utf-8"))

TASK = """# Task 12

## Scenarios

### US-312 the counter shows one after I press Add
Given a counter at 0
When I press Add
Then it shows 1
And nothing else changes

### US-new a story not written yet
- Given a
- When b
- Then c

### Scenario: The old form still works
- Given x
- When y
- But z
- Then w

## Notes
### Not a scenario
Given this is not read
"""


def test_headings_with_an_id_without_one_and_with_scenario_prefix():
    scenarios = parse_scenarios(TASK, source="task.md")
    assert [(s.id, s.title, s.name) for s in scenarios] == [
        ("US-312", "the counter shows one after I press Add", "US-312 the counter shows one after I press Add"),
        ("US-new", "a story not written yet", "US-new a story not written yet"),
        (None, "The old form still works", "The old form still works"),
    ]


def test_steps_keep_their_order_and_and_but_take_the_kind_above():
    first, _, third = parse_scenarios(TASK)
    assert [s.full for s in first.steps] == ["Given a counter at 0", "When I press Add", "Then it shows 1",
                                             "Then nothing else changes"]
    assert [(s.keyword, s.kind) for s in third.steps] == [("Given", "Given"), ("When", "When"), ("But", "When"),
                                                          ("Then", "Then")]
    assert first.steps[0].line == 6


def test_scenario_lines_work_outside_the_section_and_in_a_gherkin_block():
    text = "# T\n```gherkin\nScenario: Add a task\n  Given I am signed in\n  When I add it\n  Then I see it\n```\n"
    [scenario] = parse_scenarios(text)
    assert scenario.title == "Add a task" and len(scenario.steps) == 3


def test_and_without_a_step_above_is_an_error():
    with pytest.raises(ValueError, match="needs a Given, When or Then"):
        parse_scenarios("## Scenarios\n### A\nAnd nothing\n")


@pytest.mark.parametrize("case", CASES["matches"], ids=lambda c: c["step"])
def test_values_quoted_bare_and_numbers(case):
    assert match_pattern(compile_pattern(case["pattern"]), case["step"]) == case["values"]


def test_a_pattern_starts_with_a_keyword_and_names_each_place_once():
    with pytest.raises(ValueError, match="starts with Given"):
        compile_pattern("I add {x}")
    with pytest.raises(ValueError, match="twice"):
        compile_pattern("When I move {x} to {x}")


def test_a_bare_value_has_no_spaces():
    assert match_pattern(compile_pattern("When I delete {title}"), "When I delete Buy milk") is None


@pytest.mark.parametrize("case", CASES["nearest"], ids=lambda c: c["step"])
def test_nearest_known_steps(case):
    assert nearest(case["step"], CASES["patterns"]) == case["nearest"]


def test_shape_and_similarity():
    assert shape('When I add the task "Buy milk"') == shape("When I add the task {title}") == "when i add the task {}"
    assert similarity("When I add the task {t}", 'When I add the task "x"') == 1.0
    assert similarity("Then the list is empty", "Given a habit") < 0.5
