"""tools/vocab.py: a task's scenarios use only known steps; unknown ones get the nearest; values are typed."""
import json

from tools_path import ROOT
import vocab

TASK_VOCAB = ROOT / "recipes/shared/task-example.vocab.json"
BLOCK_VOCAB = ROOT / "functional/blocks/vocabulary.json"


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_the_example_task_uses_only_known_steps_at_every_level(capsys):
    for level in ("unit", "integration", "e2e"):
        assert vocab.main(["check", str(ROOT / "recipes/shared/task-example.md"), "--vocab", str(TASK_VOCAB), "--level", level]) == 0
    assert "Every step is a known step." in capsys.readouterr().out


def test_an_unknown_step_fails_with_the_nearest(tmp_path, capsys):
    task = write(tmp_path, "t.md", "## Scenarios\n### US-1 Add\nGiven I am signed in with an empty list\n"
                                   "When I add task Buy milk\nThen the list is empty\n")
    assert vocab.main(["check", str(task), "--vocab", str(TASK_VOCAB)]) == 1
    out = capsys.readouterr().out
    assert "NO  " in out and "t.md:4" in out and "When I add the task {title}" in out and "goes in quotes" in out


def test_values_are_typed_and_the_block_is_named(tmp_path):
    entries = vocab.load([BLOCK_VOCAB])
    assert vocab.check_step("Then the table shows 3 rows", entries, "e2e")[0]["block"] == "DataTable"
    assert "whole number" in vocab.check_step("Then the table shows many rows", entries, None)[1]
    assert "must be one of 'Empty'" in vocab.check_step('Then the log in form is in the "empty" state', entries, None)[1]
    assert vocab.check_step('Then the log in form is in the "Sending" state', entries, None)[0]["block"] == "LogIn"
    assert "no unit function" in vocab.check_step("Then the table shows 3 rows", entries, "unit")[1]


def test_both_vocabularies_together_have_no_ambiguous_step(tmp_path):
    entries = vocab.load([TASK_VOCAB, BLOCK_VOCAB])
    texts = [e["step"] for e in entries]
    assert len(texts) == len(set(texts))
    for entry in entries:  # each step, with sample values, matches only itself
        sample = entry["step"]
        for name in entry["compiled"][1]:
            kind = entry.get("params", {}).get(name, "text")
            value = kind["one_of"][0] if isinstance(kind, dict) else ("3" if kind == "int" else '"x"')
            sample = sample.replace("{" + name + "}", f'"{value}"' if isinstance(kind, dict) else value)
        found, problem = vocab.check_step(sample, entries, None)
        assert problem is None and found["step"] == entry["step"], (sample, problem)


def test_validate_finds_broken_vocabulary_files(tmp_path):
    bad = write(tmp_path, "v.json", json.dumps({"steps": [
        {"step": "I add {x}"}, {"step": "When I add {x}", "params": {"y": "text"}},
        {"step": "When I add {x}"}, {"step": "Then I see {n}", "params": {"n": "number"}, "levels": ["browser"]}]}))
    problems = vocab.validate([bad])
    assert any("starts with Given" in p for p in problems)
    assert any("declares 'y'" in p for p in problems)
    assert any("is also in" in p for p in problems)
    assert any("must be 'text', 'int'" in p for p in problems)
    assert any("unknown level 'browser'" in p for p in problems)
    assert vocab.main(["validate", str(TASK_VOCAB), str(BLOCK_VOCAB)]) == 0


def test_list_and_suggest(capsys):
    assert vocab.main(["list", str(BLOCK_VOCAB)]) == 0
    assert "When I sort by {column}  [DataTable]  (e2e)" in capsys.readouterr().out
    assert vocab.main(["suggest", "When I sort the table by Word", "--vocab", str(BLOCK_VOCAB)]) == 1
    assert capsys.readouterr().out.splitlines()[0] == "When I sort by {column}"
    assert vocab.main(["suggest", "When I sort by Word", "--vocab", str(BLOCK_VOCAB)]) == 0
