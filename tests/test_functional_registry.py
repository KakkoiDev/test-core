"""functional/registry.py: one phrase per meaning, one function per level, registries compose."""
import pytest

from functional import AmbiguousStep, Registry, StepNotAtLevel, UnknownStep


def make() -> Registry:
    steps = Registry()

    @steps.step("When I add the task {title}", level="unit")
    def add_unit(world, title):
        return ("unit", title)

    @steps.step("When I add the task {title}", level=("integration", "e2e"))
    def add_other(world, title):
        return ("other", title)

    @steps.step("Then the list is empty")
    def empty(world):
        return "empty"

    return steps


def test_find_picks_the_function_of_the_level():
    steps = make()
    definition, values = steps.find('When I add the task "Buy milk"', "unit")
    assert definition.fn(None, **values) == ("unit", "Buy milk")
    definition, values = steps.find("When I add the task milk", "e2e")
    assert definition.fn(None, **values) == ("other", "milk")
    assert steps.find("Then the list is empty", "integration")[0].levels == ("unit", "integration", "e2e")


def test_an_unknown_step_lists_the_nearest_known_steps():
    with pytest.raises(UnknownStep) as error:
        make().find("When I add task Buy milk", "unit")
    assert "Nearest known steps" in str(error.value) and "When I add the task {title}" in str(error.value)
    assert 'goes in quotes' in str(error.value)


def test_a_known_step_without_a_function_at_the_level_says_which_levels_it_has():
    steps = Registry()
    steps.add("Then I see {x}", lambda world, x: None, level="unit")
    with pytest.raises(StepNotAtLevel, match=r"no e2e implementation \(it has: unit\)"):
        steps.find("Then I see hello", "e2e")


def test_two_phrases_matching_the_same_words_are_ambiguous():
    steps = Registry()
    steps.add("Then I see {text}", lambda world, text: None)
    steps.add("Then I see {a} and {b}", lambda world, a, b: None)
    assert steps.find('Then I see "x"', "unit")[1] == {"text": "x"}  # one word: only the first phrase matches
    steps.add("Then I see {thing}s", lambda world, thing: None)
    with pytest.raises(AmbiguousStep, match="more than one"):
        steps.find("Then I see apples", "unit")


def test_registering_a_phrase_twice_at_one_level_fails():
    steps = make()
    with pytest.raises(ValueError, match="already registered at unit"):
        steps.add("When I add the task {title}", lambda world, title: None, level="unit")
    with pytest.raises(ValueError, match="level must be among"):
        steps.add("Then x", lambda world: None, level="browser")
    with pytest.raises(ValueError, match="starts with Given"):
        steps.add("see x", lambda world: None)


def test_registries_compose_and_keep_their_block():
    app = make()
    block = Registry(block="LogIn")
    block.add("When I press Log In", lambda world: None, level="e2e")
    both = Registry(app, block)
    assert both.patterns() == ["When I add the task {title}", "Then the list is empty", "When I press Log In"]
    assert both.find("When I press Log In", "e2e")[0].block == "LogIn"
    assert both.patterns("unit") == ["When I add the task {title}", "Then the list is empty"]


def test_vocabulary_and_its_check():
    steps = make()
    vocabulary = steps.vocabulary("tasks")
    assert vocabulary["steps"][0] == {"step": "When I add the task {title}", "levels": ["unit", "integration", "e2e"]}
    assert steps.check_vocabulary(vocabulary) == []
    vocabulary["steps"].append({"step": "When I delete {title}"})
    vocabulary["steps"][1]["levels"] = ["unit", "e2e"]
    del vocabulary["steps"][0]
    problems = steps.check_vocabulary(vocabulary)
    assert "no function for the step 'When I delete {title}'" in problems
    assert "the step 'When I add the task {title}' is not in the vocabulary file" in problems
